from datetime import date, datetime, timedelta, timezone
from typing import Callable
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    PayloadTooLargeException,
)
from app.db.models.overtime_requests import (
    OvertimeRequest,
    OvertimeRequestEvent,
    OvertimeRequestEventType,
    OvertimeRequestStatus,
)
from app.db.models.usuarios import Rol, Usuario
from app.db.repositories.overtime_requests import OvertimeRequestRepository
from app.schemas.overtime_requests import (
    OvertimeAdjustAndApproveRequest,
    OvertimeApproveRequest,
    OvertimeCatalogItem,
    OvertimeRejectRequest,
    OvertimeRequestCreate,
    OvertimeRequestDetail,
    OvertimeRequestEventOut,
    OvertimeRequestPage,
    OvertimeRequestSummary,
    OvertimeRequestUpdate,
)
from app.services.overtime.calculator import OvertimeValidationError, calculate_overtime
from app.services.overtime.report_renderer import OvertimePdfRenderer
from app.services.overtime.xlsx_renderer import OvertimeXlsxRenderer


class OvertimeRequestService:
    PANAMA_TZ = ZoneInfo("America/Panama")
    ACTIVE_OVERLAP_CONSTRAINT = "excl_overtime_requests_active_overlap"
    ACTIVE_OVERLAP_DETAIL = (
        "Ya existe una solicitud activa que se solapa con la fecha y el horario indicados."
    )
    PDF_MAX_REQUESTS = 2000
    XLSX_MAX_REQUESTS = 10000
    STATUS_LABELS = {
        OvertimeRequestStatus.PENDING: "Pendiente",
        OvertimeRequestStatus.APPROVED: "Aprobada",
        OvertimeRequestStatus.ADJUSTED: "Ajustada y aprobada",
        OvertimeRequestStatus.REJECTED: "Rechazada",
        OvertimeRequestStatus.CANCELLED: "Cancelada",
    }

    def __init__(
        self,
        db,
        repository: OvertimeRequestRepository | None = None,
        clock: Callable[[], datetime] | None = None,
        pdf_renderer: OvertimePdfRenderer | None = None,
        xlsx_renderer: OvertimeXlsxRenderer | None = None,
    ):
        self.db = db
        self.repository = repository or OvertimeRequestRepository(db)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.pdf_renderer = pdf_renderer
        self.xlsx_renderer = xlsx_renderer

    async def _current_db_user(self, current_user, required_role: Rol) -> Usuario:
        user = await self.repository.get_user_by_uid(current_user.uid)
        if user is None or user.company_id is None:
            raise ForbiddenException("El usuario autenticado no tiene acceso operativo")
        if user.rol != required_role or not user.is_active:
            raise ForbiddenException("El usuario autenticado no tiene el rol activo requerido")
        return user

    async def list_project_catalog(self, current_user) -> list[OvertimeCatalogItem]:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        projects = await self.repository.list_active_projects(technician.company_id)
        return [OvertimeCatalogItem(id=project.id, name=project.nombre) for project in projects]

    async def list_supervisor_catalog(self, current_user) -> list[OvertimeCatalogItem]:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        supervisors = await self.repository.list_active_supervisors(technician.company_id)
        return [OvertimeCatalogItem(id=user.id, name=user.display_name) for user in supervisors]

    async def list_technician_catalog_for_supervisor(
        self, current_user
    ) -> list[OvertimeCatalogItem]:
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        technicians = await self.repository.list_active_technicians(supervisor.company_id)
        return [OvertimeCatalogItem(id=user.id, name=user.display_name) for user in technicians]

    async def create_request(self, current_user, payload: OvertimeRequestCreate) -> OvertimeRequestDetail:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        project = await self.repository.get_active_project(technician.company_id, payload.project_id)
        if project is None:
            raise BadRequestException("El proyecto seleccionado no es válido para la compañía")
        supervisor = await self.repository.get_active_supervisor(
            technician.company_id, payload.authorizing_supervisor_id
        )
        if supervisor is None:
            raise BadRequestException("El supervisor seleccionado no es válido para la compañía")
        calculation = self._calculate(payload, payload.work_date, validate_week=True)
        if await self.repository.has_active_overlap(
            company_id=technician.company_id,
            technician_id=technician.id,
            work_date=payload.work_date,
            entry_time=payload.entry_time,
            exit_time=payload.exit_time,
        ):
            raise ConflictException(self.ACTIVE_OVERLAP_DETAIL)
        now = self.clock()
        request = OvertimeRequest(
            company_id=technician.company_id,
            technician_id=technician.id,
            work_date=payload.work_date,
            entry_time=payload.entry_time,
            break_start_time=payload.break_start_time,
            break_end_time=payload.break_end_time,
            exit_time=payload.exit_time,
            activity=payload.activity,
            project_id=project.id,
            authorizing_supervisor_id=supervisor.id,
            worked_minutes=calculation.worked_minutes,
            regular_minutes=calculation.regular_minutes,
            overtime_minutes=calculation.overtime_minutes,
            status=OvertimeRequestStatus.PENDING,
            submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        request.project = project
        request.technician = technician
        request.authorizing_supervisor = supervisor
        request.events = []
        try:
            await self.repository.create_request(request)
        except IntegrityError as exc:
            if self._constraint_name(exc) == self.ACTIVE_OVERLAP_CONSTRAINT:
                raise ConflictException(self.ACTIVE_OVERLAP_DETAIL) from exc
            raise
        event = OvertimeRequestEvent(
            overtime_request=request,
            company_id=request.company_id,
            actor_user_id=technician.id,
            event_type=OvertimeRequestEventType.SUBMITTED,
            previous_status=None,
            new_status=OvertimeRequestStatus.PENDING,
            snapshot_before=None,
            snapshot_after=self.snapshot(request),
            created_at=now,
        )
        await self.repository.create_event(event)
        return self.to_detail(request)

    async def list_own_requests(
        self, current_user, *, status, date_from, date_to, skip, limit
    ) -> list[OvertimeRequestSummary]:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        self._validate_date_range(date_from, date_to)
        rows = await self.repository.list_for_technician(
            company_id=technician.company_id, technician_id=technician.id, status=status,
            date_from=date_from, date_to=date_to, skip=skip, limit=limit
        )
        return [self.to_summary(row) for row in rows]

    async def page_own_requests(
        self, current_user, *, status, date_from, date_to, page, page_size
    ) -> OvertimeRequestPage:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        effective_from, effective_to = self._effective_page_range(date_from, date_to)
        rows, total = await self.repository.page_for_technician(
            company_id=technician.company_id,
            technician_id=technician.id,
            status=status,
            date_from=effective_from,
            date_to=effective_to,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return self._to_page(rows, page, page_size, total, effective_from, effective_to)

    async def get_own_request(self, current_user, request_id: UUID) -> OvertimeRequestDetail:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        row = await self.repository.get_for_technician(
            request_id=request_id, company_id=technician.company_id, technician_id=technician.id
        )
        if row is None:
            raise NotFoundException("Solicitud de horas extra no encontrada")
        return self.to_detail(row)

    async def update_own_request(
        self, current_user, request_id: UUID, payload: OvertimeRequestUpdate
    ) -> OvertimeRequestDetail:
        technician, request = await self._lock_pending_for_technician(current_user, request_id)
        values = {
            "work_date": request.work_date,
            "entry_time": request.entry_time,
            "break_start_time": request.break_start_time,
            "break_end_time": request.break_end_time,
            "exit_time": request.exit_time,
            "activity": request.activity,
            "project_id": request.project_id,
            "authorizing_supervisor_id": request.authorizing_supervisor_id,
        }
        values.update(payload.model_dump(exclude_unset=True))
        try:
            combined = OvertimeRequestCreate(**values)
        except ValidationError as exc:
            raise BadRequestException("La combinación de campos editados no es válida") from exc
        project = await self.repository.get_active_project(technician.company_id, combined.project_id)
        if project is None:
            raise BadRequestException("El proyecto seleccionado no es válido para la compañía")
        supervisor = await self.repository.get_active_supervisor(
            technician.company_id, combined.authorizing_supervisor_id
        )
        if supervisor is None:
            raise BadRequestException("El supervisor seleccionado no es válido para la compañía")
        calculation = self._calculate(combined, combined.work_date, validate_week=True)
        if await self.repository.has_active_overlap(
            company_id=technician.company_id,
            technician_id=technician.id,
            work_date=combined.work_date,
            entry_time=combined.entry_time,
            exit_time=combined.exit_time,
            exclude_request_id=request.id,
        ):
            raise ConflictException(self.ACTIVE_OVERLAP_DETAIL)

        before = self.snapshot(request)
        for field_name in (
            "work_date", "entry_time", "break_start_time", "break_end_time", "exit_time",
            "activity", "project_id", "authorizing_supervisor_id",
        ):
            setattr(request, field_name, getattr(combined, field_name))
        request.project = project
        request.authorizing_supervisor = supervisor
        request.worked_minutes = calculation.worked_minutes
        request.regular_minutes = calculation.regular_minutes
        request.overtime_minutes = calculation.overtime_minutes
        request.updated_at = self.clock()
        await self._create_technician_event(
            request, technician, OvertimeRequestEventType.EDITED, before
        )
        return self.to_detail(request)

    async def cancel_own_request(self, current_user, request_id: UUID) -> OvertimeRequestDetail:
        technician, request = await self._lock_pending_for_technician(current_user, request_id)
        before = self.snapshot(request)
        request.status = OvertimeRequestStatus.CANCELLED
        request.updated_at = self.clock()
        await self._create_technician_event(
            request, technician, OvertimeRequestEventType.CANCELLED, before
        )
        return self.to_detail(request)

    async def list_assigned_requests(
        self, current_user, *, status, technician_id, date_from, date_to, skip, limit
    ) -> list[OvertimeRequestSummary]:
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        self._validate_date_range(date_from, date_to)
        rows = await self.repository.list_for_supervisor(
            company_id=supervisor.company_id, supervisor_id=supervisor.id, status=status,
            technician_id=technician_id, date_from=date_from, date_to=date_to,
            skip=skip, limit=limit
        )
        return [self.to_summary(row) for row in rows]

    async def page_assigned_requests(
        self, current_user, *, status, technician_id, date_from, date_to, page, page_size
    ) -> OvertimeRequestPage:
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        effective_from, effective_to = self._effective_page_range(date_from, date_to)
        rows, total = await self.repository.page_for_supervisor(
            company_id=supervisor.company_id,
            supervisor_id=supervisor.id,
            status=status,
            technician_id=technician_id,
            date_from=effective_from,
            date_to=effective_to,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return self._to_page(rows, page, page_size, total, effective_from, effective_to)

    async def export_assigned_requests_pdf(
        self, current_user, *, status, technician_id, date_from, date_to
    ) -> tuple[bytes, date, date]:
        content, _, filename = await self.export_assigned_requests(
            current_user, export_format="pdf", status=status, technician_id=technician_id,
            date_from=date_from, date_to=date_to,
        )
        dates = filename.removeprefix("horas-extra_").removesuffix(".pdf").split("_")
        return content, date.fromisoformat(dates[0]), date.fromisoformat(dates[1])

    async def export_assigned_requests(
        self, current_user, *, export_format, status, technician_id, date_from, date_to
    ) -> tuple[bytes, str, str]:
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        effective_from, effective_to = self._effective_page_range(date_from, date_to)
        filters = {
            "company_id": supervisor.company_id,
            "supervisor_id": supervisor.id,
            "status": status,
            "technician_id": technician_id,
            "date_from": effective_from,
            "date_to": effective_to,
        }
        total = await self.repository.count_for_supervisor_export(**filters)
        limit = self.PDF_MAX_REQUESTS if export_format == "pdf" else self.XLSX_MAX_REQUESTS
        if total > limit:
            if export_format == "xlsx":
                raise PayloadTooLargeException(
                    "El reporte supera el máximo de 10000 solicitudes para XLSX. "
                    "Reduce el período o aplica más filtros."
                )
            raise PayloadTooLargeException(
                "El reporte supera el máximo de 2000 solicitudes. "
                "Reduce el período o aplica más filtros."
            )
        rows = await self.repository.list_for_supervisor_export(**filters)
        context = self._build_pdf_context(
            rows=rows,
            supervisor=supervisor,
            status=status,
            technician_id=technician_id,
            date_from=effective_from,
            date_to=effective_to,
            generated_at=self._panama_now(),
        )
        if export_format == "pdf":
            renderer = self.pdf_renderer or OvertimePdfRenderer()
            media_type = "application/pdf"
        else:
            renderer = self.xlsx_renderer or OvertimeXlsxRenderer()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"horas-extra_{effective_from}_{effective_to}.{export_format}"
        return renderer.render(context), media_type, filename

    async def get_assigned_request(self, current_user, request_id: UUID) -> OvertimeRequestDetail:
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        row = await self.repository.get_for_supervisor(
            request_id=request_id, company_id=supervisor.company_id, supervisor_id=supervisor.id
        )
        if row is None:
            raise NotFoundException("Solicitud de horas extra no encontrada")
        return self.to_detail(row)

    async def approve(
        self, current_user, request_id: UUID, payload: OvertimeApproveRequest
    ) -> OvertimeRequestDetail:
        return await self._review(
            current_user, request_id, status=OvertimeRequestStatus.APPROVED,
            event_type=OvertimeRequestEventType.APPROVED, note=payload.note
        )

    async def reject(
        self, current_user, request_id: UUID, payload: OvertimeRejectRequest
    ) -> OvertimeRequestDetail:
        return await self._review(
            current_user, request_id, status=OvertimeRequestStatus.REJECTED,
            event_type=OvertimeRequestEventType.REJECTED, note=payload.note
        )

    async def adjust_and_approve(
        self, current_user, request_id: UUID, payload: OvertimeAdjustAndApproveRequest
    ) -> OvertimeRequestDetail:
        supervisor, request = await self._lock_pending(current_user, request_id)
        project = await self.repository.get_active_project(supervisor.company_id, payload.project_id)
        if project is None:
            raise BadRequestException("El proyecto seleccionado no es válido para la compañía")
        before = self.snapshot(request)
        calculation = self._calculate(payload, request.work_date, validate_week=False)
        request.entry_time = payload.entry_time
        request.break_start_time = payload.break_start_time
        request.break_end_time = payload.break_end_time
        request.exit_time = payload.exit_time
        request.activity = payload.activity
        request.project_id = project.id
        request.project = project
        request.worked_minutes = calculation.worked_minutes
        request.regular_minutes = calculation.regular_minutes
        request.overtime_minutes = calculation.overtime_minutes
        self._apply_review(
            request, supervisor, OvertimeRequestStatus.ADJUSTED, payload.note
        )
        await self._create_review_event(
            request, supervisor, OvertimeRequestEventType.ADJUSTED_AND_APPROVED,
            before, payload.note
        )
        return self.to_detail(request)

    async def _review(self, current_user, request_id, *, status, event_type, note):
        supervisor, request = await self._lock_pending(current_user, request_id)
        before = self.snapshot(request)
        self._apply_review(request, supervisor, status, note)
        await self._create_review_event(request, supervisor, event_type, before, note)
        return self.to_detail(request)

    async def _lock_pending(self, current_user, request_id):
        supervisor = await self._current_db_user(current_user, Rol.SUPERVISOR)
        request = await self.repository.lock_for_supervisor_review(
            request_id=request_id, company_id=supervisor.company_id, supervisor_id=supervisor.id
        )
        if request is None:
            raise NotFoundException("Solicitud de horas extra no encontrada")
        if request.status != OvertimeRequestStatus.PENDING:
            raise ConflictException("La solicitud ya fue resuelta")
        return supervisor, request

    async def _lock_pending_for_technician(self, current_user, request_id):
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        request = await self.repository.lock_for_technician_mutation(
            request_id=request_id,
            company_id=technician.company_id,
            technician_id=technician.id,
        )
        if request is None:
            raise NotFoundException("Solicitud de horas extra no encontrada")
        if request.status != OvertimeRequestStatus.PENDING:
            raise ConflictException("La solicitud ya no está pendiente")
        return technician, request

    def _apply_review(self, request, supervisor, status, note):
        now = self.clock()
        request.status = status
        request.reviewed_at = now
        request.reviewed_by_user_id = supervisor.id
        request.reviewed_by_user = supervisor
        request.supervisor_note = note
        request.updated_at = now

    async def _create_review_event(self, request, supervisor, event_type, before, note):
        event = OvertimeRequestEvent(
            overtime_request=request,
            company_id=request.company_id,
            actor_user_id=supervisor.id,
            event_type=event_type,
            previous_status=OvertimeRequestStatus.PENDING,
            new_status=request.status,
            note=note,
            snapshot_before=before,
            snapshot_after=self.snapshot(request),
            created_at=self.clock(),
        )
        try:
            await self.repository.create_event(event)
        except IntegrityError as exc:
            if self._constraint_name(exc) == self.ACTIVE_OVERLAP_CONSTRAINT:
                raise ConflictException(self.ACTIVE_OVERLAP_DETAIL) from exc
            raise

    async def _create_technician_event(self, request, technician, event_type, before):
        event = OvertimeRequestEvent(
            overtime_request=request,
            company_id=request.company_id,
            actor_user_id=technician.id,
            event_type=event_type,
            previous_status=OvertimeRequestStatus.PENDING,
            new_status=request.status,
            snapshot_before=before,
            snapshot_after=self.snapshot(request),
            created_at=self.clock(),
        )
        try:
            await self.repository.create_event(event)
        except IntegrityError as exc:
            if self._constraint_name(exc) == self.ACTIVE_OVERLAP_CONSTRAINT:
                raise ConflictException(self.ACTIVE_OVERLAP_DETAIL) from exc
            raise

    def _calculate(self, payload, work_date, *, validate_week: bool):
        try:
            return calculate_overtime(
                work_date=work_date,
                entry_time=payload.entry_time,
                break_start_time=payload.break_start_time,
                break_end_time=payload.break_end_time,
                exit_time=payload.exit_time,
                now=self.clock(),
                validate_week=validate_week,
            )
        except OvertimeValidationError as exc:
            raise BadRequestException(str(exc)) from exc

    @staticmethod
    def _constraint_name(exc: IntegrityError) -> str | None:
        current: BaseException | None = exc
        visited: set[int] = set()
        while current is not None and id(current) not in visited:
            visited.add(id(current))
            name = getattr(getattr(current, "diag", None), "constraint_name", None)
            if name is None:
                name = getattr(current, "constraint_name", None)
            if name is not None:
                return name
            current = current.__cause__ or current.__context__
            if current is None and exc.orig is not exc:
                current = exc.orig
        return None

    @staticmethod
    def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from and date_to and date_from > date_to:
            raise BadRequestException("date_from no puede ser posterior a date_to")

    def _effective_page_range(
        self, date_from: date | None, date_to: date | None
    ) -> tuple[date, date]:
        if date_from is None and date_to is None:
            date_to = self._panama_now().date()
            date_from = date_to - timedelta(days=30)
        elif date_from is None:
            date_from = date_to - timedelta(days=30)
        elif date_to is None:
            date_to = date_from + timedelta(days=30)
        if date_from > date_to:
            raise BadRequestException("date_from no puede ser posterior a date_to")
        if (date_to - date_from).days + 1 > 366:
            raise BadRequestException("El rango de fechas no puede superar 366 días inclusivos")
        return date_from, date_to

    def _panama_now(self) -> datetime:
        now = self.clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.PANAMA_TZ)
        return now.astimezone(self.PANAMA_TZ)

    @staticmethod
    def _format_minutes(minutes: int) -> str:
        hours, remainder = divmod(minutes, 60)
        return f"{hours:02d}:{remainder:02d}"

    @classmethod
    def _build_pdf_context(
        cls, *, rows, supervisor, status, technician_id, date_from, date_to, generated_at
    ) -> dict:
        totals_by_technician = {}
        report_rows = []
        grand = {"count": 0, "worked": 0, "regular": 0, "overtime": 0}
        for row in rows:
            key = row.technician_id
            totals = totals_by_technician.setdefault(
                key,
                {
                    "technician": row.technician.display_name,
                    "count": 0,
                    "worked": 0,
                    "regular": 0,
                    "overtime": 0,
                },
            )
            totals["count"] += 1
            totals["worked"] += row.worked_minutes
            totals["regular"] += row.regular_minutes
            totals["overtime"] += row.overtime_minutes
            grand["count"] += 1
            grand["worked"] += row.worked_minutes
            grand["regular"] += row.regular_minutes
            grand["overtime"] += row.overtime_minutes
            break_time = "No aplica"
            if row.break_start_time is not None:
                break_time = (
                    f"{row.break_start_time.strftime('%H:%M')}–"
                    f"{row.break_end_time.strftime('%H:%M')}"
                )
            report_rows.append(
                {
                    "technician": row.technician.display_name,
                    "project": row.project.nombre,
                    "work_date": row.work_date.isoformat(),
                    "work_date_value": row.work_date,
                    "entry_time_value": row.entry_time,
                    "break_start_time_value": row.break_start_time,
                    "break_end_time_value": row.break_end_time,
                    "exit_time_value": row.exit_time,
                    "schedule": f"{row.entry_time.strftime('%H:%M')}–{row.exit_time.strftime('%H:%M')}",
                    "break_time": break_time,
                    "activity": row.activity,
                    "worked_minutes": row.worked_minutes,
                    "regular_minutes": row.regular_minutes,
                    "overtime_minutes": row.overtime_minutes,
                    "worked": cls._format_minutes(row.worked_minutes),
                    "regular": cls._format_minutes(row.regular_minutes),
                    "overtime": cls._format_minutes(row.overtime_minutes),
                    "status": cls.STATUS_LABELS[row.status],
                }
            )

        def formatted_total(total):
            return {
                **total,
                "worked_minutes": total["worked"],
                "regular_minutes": total["regular"],
                "overtime_minutes": total["overtime"],
                "worked": cls._format_minutes(total["worked"]),
                "regular": cls._format_minutes(total["regular"]),
                "overtime": cls._format_minutes(total["overtime"]),
            }

        company = supervisor.__dict__.get("company")
        return {
            "rows": report_rows,
            "technician_totals": [
                formatted_total(total) for total in totals_by_technician.values()
            ],
            "grand_total": formatted_total(grand),
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "generated_at": generated_at.strftime("%Y-%m-%d %H:%M"),
            "company_name": company.nombre if company is not None else "No disponible",
            "status_filter": cls.STATUS_LABELS[status] if status is not None else "Todos",
            "technician_filter": "Técnico seleccionado" if technician_id is not None else "Todos",
        }

    @classmethod
    def _to_page(cls, rows, page, page_size, total, date_from, date_to):
        return OvertimeRequestPage(
            items=[cls.to_summary(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size if total else 0,
            date_from=date_from,
            date_to=date_to,
        )

    @staticmethod
    def snapshot(request: OvertimeRequest) -> dict:
        def value(item):
            if item is None:
                return None
            if hasattr(item, "value"):
                return item.value
            if isinstance(item, (date, datetime)):
                return item.isoformat()
            if hasattr(item, "isoformat"):
                result = item.isoformat(timespec="minutes")
                return result
            if isinstance(item, UUID):
                return str(item)
            return item

        fields = (
            "id", "company_id", "technician_id", "work_date", "entry_time",
            "break_start_time", "break_end_time", "exit_time", "activity", "project_id",
            "authorizing_supervisor_id", "worked_minutes", "regular_minutes",
            "overtime_minutes", "status", "reviewed_at", "reviewed_by_user_id",
            "supervisor_note",
        )
        return {field: value(getattr(request, field)) for field in fields}

    @staticmethod
    def to_summary(request: OvertimeRequest) -> OvertimeRequestSummary:
        return OvertimeRequestSummary(
            id=request.id,
            work_date=request.work_date,
            activity=request.activity,
            project=OvertimeCatalogItem(id=request.project_id, name=request.project.nombre),
            technician=OvertimeCatalogItem(id=request.technician_id, name=request.technician.display_name),
            authorizing_supervisor=OvertimeCatalogItem(
                id=request.authorizing_supervisor_id, name=request.authorizing_supervisor.display_name
            ),
            worked_minutes=request.worked_minutes,
            regular_minutes=request.regular_minutes,
            overtime_minutes=request.overtime_minutes,
            status=request.status,
            submitted_at=request.submitted_at,
            reviewed_at=request.reviewed_at,
        )

    @classmethod
    def to_detail(cls, request: OvertimeRequest) -> OvertimeRequestDetail:
        summary = cls.to_summary(request).model_dump()
        events = sorted(request.events, key=lambda event: event.created_at)
        return OvertimeRequestDetail(
            **summary,
            entry_time=request.entry_time,
            break_start_time=request.break_start_time,
            break_end_time=request.break_end_time,
            exit_time=request.exit_time,
            supervisor_note=request.supervisor_note,
            created_at=request.created_at,
            updated_at=request.updated_at,
            events=[OvertimeRequestEventOut.model_validate(event) for event in events],
        )
