from datetime import date, datetime, timezone
from typing import Callable
from uuid import UUID

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
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
    OvertimeRequestSummary,
)
from app.services.overtime.calculator import OvertimeValidationError, calculate_overtime


class OvertimeRequestService:
    def __init__(
        self,
        db,
        repository: OvertimeRequestRepository | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.db = db
        self.repository = repository or OvertimeRequestRepository(db)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

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
        await self.repository.create_request(request)
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

    async def get_own_request(self, current_user, request_id: UUID) -> OvertimeRequestDetail:
        technician = await self._current_db_user(current_user, Rol.TECHNICIAN)
        row = await self.repository.get_for_technician(
            request_id=request_id, company_id=technician.company_id, technician_id=technician.id
        )
        if row is None:
            raise NotFoundException("Solicitud de horas extra no encontrada")
        return self.to_detail(row)

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
        await self.repository.create_event(event)

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
    def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from and date_to and date_from > date_to:
            raise BadRequestException("date_from no puede ser posterior a date_to")

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
