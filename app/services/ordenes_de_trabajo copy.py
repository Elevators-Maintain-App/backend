# app/services/ordenes_de_trabajo.py

from typing import List
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from sqlalchemy.orm import selectinload
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.enums.tipos_orden import TipoOrden
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.enums.prioridades import Prioridad
from app.db.models.unidades import Unidad
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.tipos_orden import tipo_orden_crud
from app.db.repositories.estados_orden import estado_orden_crud
from app.db.repositories.prioridades import prioridad_crud
from app.schemas.ordenes_de_trabajo import (
    OrdenDeTrabajoCreate,
    OrdenDeTrabajoUpdate,
    OrdenTrabajoListOut,
    OrdenTrabajoDetailOut,
    OrdenDeTrabajoSummaryOut,
    OrdenDeTrabajoSummarySupervisorOut,
    OrdenDeTrabajoWeeklyComplianceOut,
)
from app.auth.firebase import get_firestore_client
from app.db.models.compania import Compania
from datetime import datetime, timedelta, date
from fastapi.concurrency import run_in_threadpool

class OrdenDeTrabajoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # — Admin —
    async def count_by_company(self, company_id: UUID) -> int:
        stmt = select(func.count()).select_from(OrdenDeTrabajo).where(OrdenDeTrabajo.company_id == company_id)
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def list_summary_by_company(self, company_id: UUID) -> List[OrdenDeTrabajoSummaryOut]:
        ordenes = await orden_de_trabajo_crud.get_multi_by_field(
            self.db, field="company_id", value=company_id
        )
        return [OrdenDeTrabajoSummaryOut.from_orm(o) for o in ordenes]

    # — Supervisor —
    async def count_by_supervisor(self, supervisor_uid: str) -> int:
        stmt = select(func.count()).select_from(OrdenDeTrabajo).where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def list_summary_by_supervisor(
        self, supervisor_uid: str, full: bool = False
    ) -> List[OrdenDeTrabajoSummarySupervisorOut]:
        """
        Si full=False, devuelve las últimas 10; si full=True, devuelve todas.
        """
        stmt = (
            select(OrdenDeTrabajo)
            .where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
            .options(
                # eager load la unidad y su proyecto
                selectinload(OrdenDeTrabajo.unidad)
                .selectinload(Unidad.proyecto)
            )
            .order_by(OrdenDeTrabajo.fecha.desc())
        )

        if not full:
            stmt = stmt.limit(10)

        res = await self.db.execute(stmt)
        out = []
        for o in res.scalars().all():
            unidad = o.unidad
            proyecto_nombre = unidad.proyecto.nombre
            estado_nombre = (await self.db.get(EstadoOrden, o.estado_id)).nombre
            out.append(
                OrdenDeTrabajoSummarySupervisorOut(
                    id=o.id,
                    proyecto_nombre=proyecto_nombre,
                    unidad_nombre=unidad.nombre,
                    fecha=o.fecha,
                    estado=estado_nombre
                )
            )
        return out
    
    async def get_detail(self, orden_id: UUID, user) -> OrdenTrabajoDetailOut:
        o = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not o:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
        # permisos
        if user.role == "admin":
            if str(o.company_id) != str(user.company_id):
                raise HTTPException(status.HTTP_403_FORBIDDEN)
        else:  # supervisor
            if o.supervisor_id != user.uid:
                raise HTTPException(status.HTTP_403_FORBIDDEN)
        # enums
        tipo = await tipo_orden_crud.get(self.db, o.tipo_orden_id)
        estado = await estado_orden_crud.get(self.db, o.estado_id)
        prioridad = await prioridad_crud.get(self.db, o.prioridad_id)
        unidad = await self.db.get(Unidad, o.unidad_id)
        # Firestore
        sup = await run_in_threadpool(lambda: get_firestore_client().collection("users").document(o.supervisor_id).get())
        tec = await run_in_threadpool(lambda: get_firestore_client().collection("users").document(o.tecnico_id).get())
        cliente = await run_in_threadpool(lambda: get_firestore_client().collection("users").document(o.tecnico_id).get())
        sup_name = sup.to_dict().get("display_name","—") if sup.exists else "—"
        tec_name = tec.to_dict().get("display_name","—") if tec.exists else "—"
        cli_name = cliente.to_dict().get("display_name","—") if cliente.exists else "—"
        comp = await self.db.get(Compania, o.company_id)
        comp_name = comp.nombre if comp else "—"
        return OrdenTrabajoDetailOut(
            id=o.id,
            referencia=o.referencia,
            fecha=o.fecha,
            descripcion=o.descripcion,
            observaciones=o.observaciones,
            valor=o.valor,
            tipo_orden=tipo.nombre if tipo else "—",
            estado=estado.nombre if estado else "—",
            prioridad=prioridad.nombre if prioridad else "—",
            unidad_id=o.unidad_id,
            supervisor_id=o.supervisor_id,
            tecnico_id=o.tecnico_id,
            cliente=cli_name,
            compania=comp_name,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )

    # — Conteo por estados para mes actual —
    async def counts_by_state_this_month(
            self, supervisor_uid: str, company_id: UUID
        ) -> dict:
            today = date.today()
            year = today.year
            month = today.month

            # 1) total de órdenes este mes
            total_stmt = select(func.count()).where(
                and_(
                    OrdenDeTrabajo.supervisor_id == supervisor_uid,
                    OrdenDeTrabajo.company_id == company_id,
                    extract("year", OrdenDeTrabajo.fecha) == year,
                    extract("month", OrdenDeTrabajo.fecha) == month,
                )
            )
            total = (await self.db.execute(total_stmt)).scalar_one()

            # 2) conteos por estado este mes
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
            counts = {estado_id: cnt for estado_id, cnt in res.all()}

            return {
                "programadas": total,
                "validadas": counts.get(3, 0),    # estado 3 = Completada
                "pendientes": counts.get(2, 0),   # estado 2 = en validación
            }

    async def weekly_compliance(self, supervisor_uid: str, company_id: UUID) -> OrdenDeTrabajoWeeklyComplianceOut:
        cnts = await self.counts_by_state_this_month(supervisor_uid, company_id)
        tot = cnts["programadas"]
        val = cnts["validadas"]
        pct = (val / tot) if tot else 0
        text = f"{int(pct*100)}%"
        detail = f"{val} de {tot} Validadas"
        return OrdenDeTrabajoWeeklyComplianceOut(text=text, value=pct, detail=detail)
    
    async def create_for_admin(
        self,
        orden_in: OrdenDeTrabajoCreate,
        supervisor_id: str,
        company_id: UUID,
        user
    ) -> OrdenTrabajoDetailOut:
        # 1) validar unidad
        unidad = await unidad_crud.get(self.db, orden_in.unidad_id)
        if not unidad or str(unidad.company_id) != str(company_id):
            raise HTTPException(status_code=400, detail="Unidad invalida")

        # 2) validar roles en Firestore
        # técnico
        tec_doc = db_firestore.collection("users").document(orden_in.tecnico_id).get()
        if not tec_doc.exists or tec_doc.to_dict().get("rol") != "technician":
            raise HTTPException(status_code=400, detail="Técnico invalido")

        # supervisor
        sup_doc = db_firestore.collection("users").document(supervisor_id).get()
        if not sup_doc.exists or sup_doc.to_dict().get("rol") != "superVisor":
            raise HTTPException(status_code=400, detail="Supervisor invalido")

        # 3) validar enums
        for repo, val, name in [
            (tipo_orden_crud, orden_in.tipo_orden_id, "tipo de orden"),
            (estado_orden_crud, orden_in.estado_id, "estado"),
            (prioridad_crud, orden_in.prioridad_id, "prioridad"),
        ]:
            if not await repo.get(self.db, val):
                raise HTTPException(status_code=400, detail=f"{name} invalido")

        # 4) preparar datos, excluyendo supervisor_id del dict
        orden_data = orden_in.dict(exclude_unset=True, exclude={"supervisor_id"})

        # 5) crear instancia
        nueva = OrdenDeTrabajo(
            **orden_data,
            id=uuid4(),
            company_id=company_id,
            supervisor_id=supervisor_id
        )

        # 6) generar referencia
        fecha = datetime.now().strftime("%y%m%d")
        seq = (await self.db.execute(
            select(func.count()).select_from(OrdenDeTrabajo)
            .where(OrdenDeTrabajo.company_id == company_id)
        )).scalar_one() + 1
        nueva.referencia = f"OTC{fecha}{seq:04d}"

        # 7) persistir
        self.db.add(nueva)
        await self.db.commit()
        await self.db.refresh(nueva)

        # 8) devolver detalle
        return await self.get_detail(nueva.id, user)