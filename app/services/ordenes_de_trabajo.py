# app/services/ordenes_de_trabajo.py

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.enums.tipos_orden import TipoOrden
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.enums.prioridades import Prioridad
from app.db.models.unidades import Unidad
from app.db.models.proyectos import Proyecto
from app.db.models.checklists import Checklist
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.tipos_orden import tipo_orden_crud
from app.db.repositories.estados_orden import estado_orden_crud
from app.db.repositories.prioridades import prioridad_crud
from app.auth.firebase import get_firestore_client
from app.db.models.compania import Compania
import logging
from app.services.cliente import ClienteService
from app.schemas.ordenes_de_trabajo import (
    OrdenDeTrabajoCreate,
    OrdenDeTrabajoUpdate,
    OrdenTrabajoDetailOut,
    OrdenDeTrabajoSummaryOut,
    OrdenDeTrabajoSummarySupervisorOut,
    OrdenDeTrabajoSummaryTechnicianOut,
    OrdenDeTrabajoWeeklyComplianceOut,
    OrdenDeTrabajoListOut
)
from app.services.plans import PlanEnforcementService

logging.basicConfig(
    level=logging.DEBUG,  # O usa logging.INFO si no necesitas tanto detalle
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OrdenDeTrabajoService:
    MAX_REFERENCE_RETRIES = 3

    def __init__(self, db: AsyncSession):
        self.db = db

    def _reference_prefix_for_today(self) -> str:
        return f"OTC{datetime.now().strftime('%y%m%d')}"

    async def _generate_next_reference(self, company_id: UUID) -> str:
        prefix = self._reference_prefix_for_today()
        stmt = (
            select(OrdenDeTrabajo.referencia)
            .where(
                OrdenDeTrabajo.company_id == company_id,
                OrdenDeTrabajo.referencia.like(f"{prefix}%")
            )
            .order_by(OrdenDeTrabajo.referencia.desc())
            .limit(1)
        )
        last_ref = (await self.db.execute(stmt)).scalar_one_or_none()

        last_seq = 0
        if last_ref:
            try:
                last_seq = int(last_ref.removeprefix(prefix))
            except ValueError:
                logger.warning("No se pudo parsear la referencia previa %s; reiniciando secuencia diaria", last_ref)

        return f"{prefix}{last_seq + 1:04d}"

    def _build_orden_entity(
        self,
        orden_data: dict,
        company_id: UUID,
        cliente_id: UUID,
        referencia: str,
    ) -> OrdenDeTrabajo:
        return OrdenDeTrabajo(
            **orden_data,
            id=uuid4(),
            referencia=referencia,
            company_id=company_id,
            cliente_id=cliente_id,
        )

    def _is_reference_unique_violation(self, error: IntegrityError) -> bool:
        constraint_names = {
            getattr(error.orig, "constraint_name", None),
            getattr(getattr(error.orig, "diag", None), "constraint_name", None),
        }
        if "ordenes_de_trabajo_referencia_key" in constraint_names:
            return True
        return "ordenes_de_trabajo_referencia_key" in str(error)

    # — Admin —
    async def count_by_company(self, company_id: UUID) -> int:
        stmt = select(func.count()).select_from(OrdenDeTrabajo).where(OrdenDeTrabajo.company_id == company_id)
        return (await self.db.execute(stmt)).scalar_one()

    async def list_summary_by_company(self, company_id: UUID) -> List[OrdenDeTrabajoSummaryOut]:
        stmt = (
            select(
                OrdenDeTrabajo.id,
                OrdenDeTrabajo.referencia,
                OrdenDeTrabajo.fecha,
                OrdenDeTrabajo.supervisor_id,
                OrdenDeTrabajo.tecnico_id,
                OrdenDeTrabajo.unidad_id,
                OrdenDeTrabajo.company_id,
                OrdenDeTrabajo.tipo_orden_id,
                OrdenDeTrabajo.estado_id,
                OrdenDeTrabajo.prioridad_id,
            )
            .where(OrdenDeTrabajo.company_id == company_id)
            .offset(0)
            .limit(100)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            OrdenDeTrabajoSummaryOut(
                id=row.id,
                referencia=row.referencia,
                fecha=row.fecha,
                supervisor_id=row.supervisor_id,
                tecnico_id=row.tecnico_id,
                unidad_id=row.unidad_id,
                company_id=row.company_id,
                tipo_orden_id=row.tipo_orden_id,
                estado_id=row.estado_id,
                prioridad_id=row.prioridad_id,
            )
            for row in rows
        ]

    # — Supervisor —
    async def count_by_supervisor(self, supervisor_uid: str) -> int:
        stmt = select(func.count()).select_from(OrdenDeTrabajo).where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
        return (await self.db.execute(stmt)).scalar_one()

    async def list_summary_by_supervisor(
        self, supervisor_uid: str, full: bool = False
    ) -> List[OrdenDeTrabajoSummarySupervisorOut]:
        stmt = (
            select(OrdenDeTrabajo)
            .where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
            .options(selectinload(OrdenDeTrabajo.unidad).selectinload(Unidad.proyecto))
            .order_by(OrdenDeTrabajo.fecha.desc())
        )
        if not full:
            stmt = stmt.limit(10)
        res = await self.db.execute(stmt)
        out = []
        for o in res.scalars().all():
            out.append(OrdenDeTrabajoSummarySupervisorOut(
                id=o.id,
                proyecto_nombre=o.unidad.proyecto.nombre,
                unidad_nombre=o.unidad.nombre,
                fecha=o.fecha,
                estado=(await self.db.get(EstadoOrden, o.estado_id)).nombre
            ))
        return out

    # — Técnico —
    async def count_by_technician(self, technician_uid: str) -> int:
        stmt = select(func.count()).select_from(OrdenDeTrabajo).where(OrdenDeTrabajo.tecnico_id == technician_uid)
        return (await self.db.execute(stmt)).scalar_one()

    async def list_summary_by_technician(
        self, technician_uid: str, full: bool = False
    ) -> List[OrdenDeTrabajoSummaryTechnicianOut]:
        stmt = (
            select(OrdenDeTrabajo)
            .where(OrdenDeTrabajo.tecnico_id == technician_uid)
            .options(selectinload(OrdenDeTrabajo.unidad).selectinload(Unidad.proyecto))
            .order_by(OrdenDeTrabajo.fecha.desc())
        )
        if not full:
            stmt = stmt.limit(10)
        res = await self.db.execute(stmt)
        out = []
        for o in res.scalars().all():
            out.append(OrdenDeTrabajoSummaryTechnicianOut(
                id=o.id,
                proyecto_nombre=o.unidad.proyecto.nombre,
                unidad_nombre=o.unidad.nombre,
                fecha=o.fecha,
                estado=(await self.db.get(EstadoOrden, o.estado_id)).nombre
            ))
        return out

    # — Detalle compartido —
    async def get_detail(self, orden_id: UUID, user) -> OrdenTrabajoDetailOut:
        # 1) Recuperar la orden
        o = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not o:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # 2) Permisos
        if user.rol.value == "admin":
            if str(o.company_id) != str(user.company_id):
                raise HTTPException(status_code=403, detail="Admin No autorizado")
        elif user.rol.value == "supervisor":
            if o.supervisor_id != user.uid:
                raise HTTPException(status_code=403, detail="SupervisorNo autorizado")
        else:  # technician
            if o.tecnico_id != user.uid:
                raise HTTPException(status_code=403, detail="Tecnico No autorizado")

        # 3) Cargar unidad + proyecto en una sola consulta        
        stmt = (
            select(Unidad)
            .options(selectinload(Unidad.proyecto))
            .where(Unidad.id == o.unidad_id)
        )
        result = await self.db.execute(stmt)
        unidad: Unidad = result.scalars().first()
        if not unidad:
            raise HTTPException(status_code=500, detail="Error interno: unidad faltante")
        proyecto_nombre = unidad.proyecto.nombre if unidad.proyecto else "—"

        # 4) Cargar nombres de enums        
        tipo   = await tipo_orden_crud.get(self.db, o.tipo_orden_id)
        estado = await estado_orden_crud.get(self.db, o.estado_id)
        prioridad = await prioridad_crud.get(self.db, o.prioridad_id)
        unidad = await self.db.get(Unidad, o.unidad_id)

        # 5) Obtener nombre de supervisor desde Firestore
        # Firestore y compañía
        sup = get_firestore_client().collection("users").document(o.supervisor_id).get()
        tec = get_firestore_client().collection("users").document(o.tecnico_id).get()
        supervisor_nombre = sup.to_dict().get("display_name","—") if sup.exists else "—"
        tec_name = tec.to_dict().get("display_name","—") if tec.exists else "—"
        comp = await self.db.get(Compania, o.company_id)

        # 6) Nombre de unidad
        unidad_nombre = unidad.nombre

        # 7) Cliente real (viene del proyecto asociado a la unidad)
        cliente_id = unidad.proyecto.cliente_id if unidad.proyecto else None
        cliente_nombre = "—"
        if cliente_id:
            cliente_serv = ClienteService(self.db)
            cli_doc = await cliente_serv.get_by_id(cliente_id, user)
            cliente_nombre = cli_doc.nombre if cli_doc else "—"

        # 8) Empaquetar solo los campos requeridos
        
        return OrdenTrabajoDetailOut(
            referencia    = o.referencia,
            descripcion   = o.descripcion,
            tipo_orden    = tipo.nombre if tipo else "—",
            proyecto      = proyecto_nombre,
            prioridad     = prioridad.nombre if prioridad else "—",
            supervisor    = supervisor_nombre,
            unidad        = unidad_nombre,
            cliente       = cliente_nombre,
            estado        = estado.nombre if estado else "—",
            observaciones = o.observaciones or ""
        )

    # — Conteos para mes actual (Supervisor) —
    async def counts_by_state_this_month(self, supervisor_uid: str, company_id: UUID) -> dict:
        today = date.today()
        year, month = today.year, today.month

        total_stmt = select(func.count()).where(
            and_(
                OrdenDeTrabajo.supervisor_id == supervisor_uid,
                OrdenDeTrabajo.company_id == company_id,
                extract("year", OrdenDeTrabajo.fecha) == year,
                extract("month", OrdenDeTrabajo.fecha) == month,
            )
        )
        total = (await self.db.execute(total_stmt)).scalar_one()

        counts_stmt = (
            select(OrdenDeTrabajo.estado_id, func.count())
            .where(
                and_(
                    OrdenDeTrabajo.supervisor_id == supervisor_uid,
                    OrdenDeTrabajo.company_id == company_id,
                    extract("year", OrdenDeTrabajo.fecha) == year,
                    extract("month", OrdenDeTrabajo.fecha) == month,
                )
            )
            .group_by(OrdenDeTrabajo.estado_id)
        )
        res = await self.db.execute(counts_stmt)
        cnts = {est: c for est, c in res.all()}

        return {
            "programadas": total,
            "validadas": cnts.get(3, 0),
            "pendientes": cnts.get(2, 0),
        }

    # — Conteos para mes actual (Técnico) —
    async def counts_by_state_this_month_technician(self, technician_uid: str, company_id: UUID) -> dict:
        today = date.today()
        year, month = today.year, today.month

        total_stmt = select(func.count()).where(
            and_(
                OrdenDeTrabajo.tecnico_id == technician_uid,
                OrdenDeTrabajo.company_id == company_id,
                extract("year", OrdenDeTrabajo.fecha) == year,
                extract("month", OrdenDeTrabajo.fecha) == month,
            )
        )
        total = (await self.db.execute(total_stmt)).scalar_one()

        counts_stmt = (
            select(OrdenDeTrabajo.estado_id, func.count())
            .where(
                and_(
                    OrdenDeTrabajo.tecnico_id == technician_uid,
                    OrdenDeTrabajo.company_id == company_id,
                    extract("year", OrdenDeTrabajo.fecha) == year,
                    extract("month", OrdenDeTrabajo.fecha) == month,
                )
            )
            .group_by(OrdenDeTrabajo.estado_id)
        )
        res = await self.db.execute(counts_stmt)
        cnts = {est: c for est, c in res.all()}

        return {
            "programadas": total,
            "validadas": cnts.get(5, 0),
            "pendientes": total - (cnts.get(5, 0) + cnts.get(4, 0)),
        }

    # — Cumplimiento mensual (Supervisor) —
    async def monthly_compliance(self, supervisor_uid: str, company_id: UUID) -> OrdenDeTrabajoWeeklyComplianceOut:
        cnts = await self.counts_by_state_this_month(supervisor_uid, company_id)
        tot, val = cnts["programadas"], cnts["validadas"]
        pct = val / tot if tot else 0
        return OrdenDeTrabajoWeeklyComplianceOut(
            text=f"{int(pct*100)}%",
            value=pct,
            detail=f"{val} de {tot} Validadas"
        )

    # — Cumplimiento mensual (Técnico) —
    async def monthly_compliance_technician(
        self, technician_uid: str, company_id: UUID
    ) -> OrdenDeTrabajoWeeklyComplianceOut:
        cnts = await self.counts_by_state_this_month_technician(technician_uid, company_id)
        tot, val = cnts["programadas"], cnts["validadas"]
        pct = val / tot if tot else 0
        return OrdenDeTrabajoWeeklyComplianceOut(
            text=f"{int(pct*100)}%",
            value=pct,
            detail=f"{val} de {tot} Completadas"
        )

    # — Update (Shared) —
    async def update(
        self, 
        orden_id: UUID, 
        orden_in: OrdenDeTrabajoUpdate, 
        user
    ) -> OrdenTrabajoDetailOut:
        # 1) Obtener orden
        o = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not o:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # 2) Validar permisos
        # super_admin pasa directo (según requerimiento)
        if user.rol.value == "admin":
            if str(o.company_id) != str(user.company_id):
                raise HTTPException(status_code=403, detail="No autorizado para editar esta orden")
        elif user.rol.value == "supervisor":
            if o.supervisor_id != user.uid:
                raise HTTPException(status_code=403, detail="No autorizado para editar esta orden")
        elif user.rol.value not in ["admin", "supervisor", "super_admin"]:
             # technician / client
             raise HTTPException(status_code=403, detail="Rol no autorizado para editar")

        # 3) Actualizar
        await orden_de_trabajo_crud.update(self.db, db_obj=o, obj_in=orden_in)

        # 4) Retornar detalle actualizado
        return await self.get_detail(orden_id, user)

    # — Delete (Shared) —
    async def delete(self, orden_id: UUID, user) -> None:
        # 1) Obtener orden
        o = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not o:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # 2) Validar permisos
        if user.rol.value == "admin":
            if str(o.company_id) != str(user.company_id):
                raise HTTPException(status_code=403, detail="No autorizado para eliminar esta orden")
        elif user.rol.value == "supervisor":
            if o.supervisor_id != user.uid:
                raise HTTPException(status_code=403, detail="No autorizado para eliminar esta orden")
        elif user.rol.value not in ["admin", "supervisor", "super_admin"]:
             raise HTTPException(status_code=403, detail="Rol no autorizado para eliminar")

        # 3) Eliminar
        try:
            await orden_de_trabajo_crud.remove(self.db, id=orden_id)
        except IntegrityError as exc:
            await self.db.rollback()
            logger.exception("Error de integridad al eliminar orden de trabajo %s", orden_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No fue posible eliminar la orden de trabajo porque tiene datos relacionados.",
            ) from exc
        return None

    # — Crear (admin) —
    async def create(
        self,
        orden_in: OrdenDeTrabajoCreate,
        company_id: UUID,
        user
    ) -> OrdenTrabajoDetailOut:
        # 1) validar unidad
        unidad = await unidad_crud.get(self.db, orden_in.unidad_id)
        if not unidad or str(unidad.company_id) != str(company_id):
            raise HTTPException(status_code=400, detail="Unidad invalida")
        
        cliente_id = unidad.cliente_id
        if not cliente_id:
            raise HTTPException(status_code=400, detail="Unidad sin cliente asignado")

        # 3) validar enums
        for repo, val, name in [
            (tipo_orden_crud, orden_in.tipo_orden_id, "tipo de orden"),
            (estado_orden_crud, orden_in.estado_id, "estado"),
            (prioridad_crud, orden_in.prioridad_id, "prioridad"),
        ]:
            if not await repo.get(self.db, val):
                raise HTTPException(status_code=400, detail=f"{name} invalido")

        plan_enforcement = PlanEnforcementService(self.db)
        await plan_enforcement.assert_can_create_work_order(company_id)

        # 4) preparar datos, excluyendo supervisor_id del dict
        orden_data = orden_in.model_dump(exclude_unset=True)

        # 5) generar referencia y persistir con reintentos acotados
        for attempt in range(self.MAX_REFERENCE_RETRIES):
            nueva = self._build_orden_entity(
                orden_data=orden_data,
                company_id=company_id,
                cliente_id=cliente_id,
                referencia=await self._generate_next_reference(company_id),
            )
            self.db.add(nueva)

            try:
                await self.db.commit()
                await self.db.refresh(nueva)
                await plan_enforcement.refresh_current_usage_snapshot(company_id)
                return nueva.id
            except IntegrityError as exc:
                await self.db.rollback()

                if self._is_reference_unique_violation(exc):
                    if attempt < self.MAX_REFERENCE_RETRIES - 1:
                        logger.warning(
                            "Colision de referencia al crear orden para company_id=%s. Reintentando (%s/%s)",
                            company_id,
                            attempt + 1,
                            self.MAX_REFERENCE_RETRIES,
                        )
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="No fue posible generar una referencia única para la orden de trabajo. Intente nuevamente.",
                    ) from exc

                raise

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible generar una referencia única para la orden de trabajo. Intente nuevamente.",
        )
    
    async def get_total_ordenes_trabajo_por_compania(self, company_id: UUID) -> int:
        return await orden_de_trabajo_crud.get_total_by_field(
            self.db,
            field="company_id",
            value=company_id
        )
    
    async def get_total_ordenes_trabajo_por_cliente(self, cliente_id: UUID) -> int:
        return await orden_de_trabajo_crud.get_total_by_field(
            self.db,
            field="cliente_id",
            value=cliente_id
        )
    
    async def get_total_ordenes_trabajo_por_proyecto(self, proyecto_id: UUID) -> int:
        return await orden_de_trabajo_crud.get_total_by_field(
            self.db,
            field="proyecto_id",
            value=proyecto_id
        )

    async def list_ordenes_supervisor_filtradas(
        self,
        supervisor_uid: str,
        estado_id: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        cliente_id: Optional[str] = None,
        tecnico_id: Optional[str] = None,
        proyecto_id: Optional[UUID] = None
    ) -> List[OrdenDeTrabajoListOut]:
        """Lista órdenes del supervisor con filtros opcionales"""
        
        query = (
            select(
                OrdenDeTrabajo.id.label('orden_id'),
                Proyecto.nombre.label('proyecto'),
                Unidad.nombre.label('unidad'),
                OrdenDeTrabajo.created_at.label('fecha'),
                EstadoOrden.nombre.label('estado'),
                OrdenDeTrabajo.descripcion,
                OrdenDeTrabajo.observaciones,
                Checklist.reporte_final_url.label('url_reporte_final'),
                Checklist.reporte_prerevision_url.label('url_prereporte')
            )
            .join(Unidad, OrdenDeTrabajo.unidad_id == Unidad.id)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .join(EstadoOrden, OrdenDeTrabajo.estado_id == EstadoOrden.id)
            .outerjoin(Checklist, Checklist.orden_trabajo_id == OrdenDeTrabajo.id)
            .where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
        )
        
        # Aplicar filtros opcionales
        if estado_id:
            query = query.where(OrdenDeTrabajo.estado_id == estado_id)
            
        if fecha_inicio:
            query = query.where(OrdenDeTrabajo.created_at >= fecha_inicio)
            
        if fecha_fin:
            query = query.where(OrdenDeTrabajo.created_at <= fecha_fin)
            
        if cliente_id:
            query = query.where(OrdenDeTrabajo.cliente_id == cliente_id)
            
        if tecnico_id:
            query = query.where(OrdenDeTrabajo.tecnico_id == tecnico_id)
            
        if proyecto_id:
            query = query.where(Unidad.proyecto_id == proyecto_id)
        
        # Ordenar por fecha descendente
        query = query.order_by(OrdenDeTrabajo.created_at.desc())
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return [
            OrdenDeTrabajoListOut(
                orden_id=row.orden_id,
                proyecto=row.proyecto,
                unidad=row.unidad,
                fecha=row.fecha,
                estado=row.estado,
                descripcion=row.descripcion,
                observaciones=row.observaciones,
                url_reporte_final=row.url_reporte_final if row.estado == "Cerrada" else None,
                url_prereporte=row.url_prereporte if row.estado == "En Validación" else None
            )
            for row in rows
        ]
