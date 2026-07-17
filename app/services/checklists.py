# app/services/checklists.py

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from zoneinfo import ZoneInfo

from app.db.models.checklists import (
    Checklist,
    ChecklistItem,
    ChecklistItemTemplate,
    ChecklistTemplate,
)
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.unidades import Unidad
from app.db.models.enums.tipos_orden import TipoOrden
from app.db.models.enums.tipos_unidad import TipoUnidad
from app.schemas.checklists import (
    ChecklistItemOut,
    ChecklistOut,
    ChecklistTemplateCreate,
    ChecklistItemTemplateOut,
    ChecklistTemplateOut,
    ChecklistTemplateOut2,
    ChecklistTemplateAdminOut,
    ChecklistItemTemplateAdminOut,
)
from app.schemas.checklists_sync import ChecklistSyncPayload


LOCAL_TZ = ZoneInfo("America/Panama")


# Helpers
# -------------------------

TimeOrDateTime = Optional[Union[datetime, time]]

def to_panama_time(value: TimeOrDateTime) -> Optional[time]:
    """
    Normaliza un valor de hora/fecha a hora local de Panamá (America/Panama) y devuelve solo el componente `time`.
    """
    if value is None:
        return None

    if isinstance(value, time):
        return value

    dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(LOCAL_TZ).time()

# Service
# -------------------------

class ChecklistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- Templates ----------

    async def list_admin_templates(self) -> list[ChecklistTemplateAdminOut]:
        """Lista el catálogo global de plantillas con sus nombres y pasos."""
        stmt = (
            select(
                ChecklistTemplate,
                TipoOrden.nombre.label("tipo_orden_nombre"),
                TipoUnidad.nombre.label("tipo_unidad_nombre"),
            )
            .outerjoin(TipoOrden, TipoOrden.id == ChecklistTemplate.tipo_orden_id)
            .outerjoin(TipoUnidad, TipoUnidad.id == ChecklistTemplate.tipo_unidad_id)
            .options(selectinload(ChecklistTemplate.pasos))
            .order_by(
                TipoOrden.nombre.asc().nulls_last(),
                TipoUnidad.nombre.asc().nulls_last(),
                ChecklistTemplate.nombre.asc(),
                ChecklistTemplate.id.asc(),
            )
        )
        rows = (await self.db.execute(stmt)).all()

        return [
            ChecklistTemplateAdminOut(
                id=template.id,
                nombre=template.nombre,
                tipo_orden_id=template.tipo_orden_id,
                tipo_orden_nombre=tipo_orden_nombre,
                tipo_unidad_id=template.tipo_unidad_id,
                tipo_unidad_nombre=tipo_unidad_nombre,
                total_steps=len(template.pasos),
                created_at=template.created_at,
                updated_at=template.updated_at,
                pasos=[
                    ChecklistItemTemplateAdminOut(
                        id=paso.id,
                        step_number=paso.step_number,
                        titulo=paso.titulo,
                        instrucciones=paso.instrucciones,
                        evidencia_schema=paso.evidencia_schema,
                    )
                    for paso in sorted(
                        template.pasos,
                        key=lambda paso: (paso.step_number, str(paso.id)),
                    )
                ],
            )
            for template, tipo_orden_nombre, tipo_unidad_nombre in rows
        ]

    async def get_template_for_order(self, orden_id: UUID) -> ChecklistTemplateOut:
        """
        Obtiene la plantilla de checklist aplicable a una orden (tipo de orden + tipo de unidad),
        e incluye pasos para inicializar el checklist.
        """
        orden = await self.db.get(OrdenDeTrabajo, orden_id)
        if not orden:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")

        unidad = await self.db.get(Unidad, orden.unidad_id)
        if not unidad:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidad no encontrada")

        stmt = (
            select(ChecklistTemplate)
            .where(
                ChecklistTemplate.tipo_orden_id == orden.tipo_orden_id,
                ChecklistTemplate.tipo_unidad_id == unidad.tipo_unidad_id,
            )
            .options(selectinload(ChecklistTemplate.pasos))
        )
        tpl = (await self.db.execute(stmt)).scalars().first()
        if not tpl:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay plantilla para esta combinación")

        pasos_out = [
            ChecklistItemTemplateOut(
                step_number=p.step_number,
                titulo=p.titulo,
                instrucciones=p.instrucciones,
                evidencia_schema=p.evidencia_schema,
            )
            for p in tpl.pasos
        ]

        total = len(pasos_out)
        step_nums = [p.step_number for p in pasos_out]
        pasos_ids = [p.id for p in tpl.pasos]

        return ChecklistTemplateOut(
            id=tpl.id,
            nombre=tpl.nombre,
            tipo_orden_id=tpl.tipo_orden_id,
            tipo_unidad_id=tpl.tipo_unidad_id,
            pasos=pasos_out,
            total_steps=total,
            step_numbers=step_nums,
            pasos_ids=pasos_ids,
            current_step=1,
        )

    async def create_template_with_items(self, payload: ChecklistTemplateCreate) -> ChecklistTemplateOut2:
        """
        Crea una plantilla de checklist y sus pasos asociados para una combinación (tipo_orden_id + tipo_unidad_id).
        """
        exists = await self.db.execute(
            select(ChecklistTemplate).where(
                ChecklistTemplate.tipo_orden_id == payload.tipo_orden_id,
                ChecklistTemplate.tipo_unidad_id == payload.tipo_unidad_id,
            )
        )
        if exists.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una plantilla para esa combinación",
            )

        template = ChecklistTemplate(
            nombre=payload.nombre,
            tipo_orden_id=payload.tipo_orden_id,
            tipo_unidad_id=payload.tipo_unidad_id,
        )
        self.db.add(template)
        await self.db.flush()  # obtener template.id

        for paso_in in payload.pasos:
            self.db.add(
                ChecklistItemTemplate(
                    checklist_template_id=template.id,
                    step_number=paso_in.step_number,
                    titulo=paso_in.titulo,
                    instrucciones=paso_in.instrucciones,
                    evidencia_schema=paso_in.evidencia_schema,
                )
            )

        await self.db.commit()
        await self.db.refresh(template)

        # Cargar pasos para obtener IDs
        loaded = await self.db.execute(
            select(ChecklistTemplate)
            .options(selectinload(ChecklistTemplate.pasos))
            .where(ChecklistTemplate.id == template.id)
        )
        template_loaded = loaded.scalars().first()
        pasos_ids = [p.id for p in (template_loaded.pasos or [])] if template_loaded else []

        return ChecklistTemplateOut2(
            id=template.id,
            nombre=template.nombre,
            tipo_orden_id=template.tipo_orden_id,
            tipo_unidad_id=template.tipo_unidad_id,
            created_at=template.created_at,
            updated_at=template.updated_at,
            pasos_ids=pasos_ids,
        )

    # ---------- Checklist lifecycle ----------

    async def init_checklist(self, orden_id: UUID) -> None:
        """
        Crea el checklist y sus items a partir de la plantilla si aún no existe para la orden.
        No hace commit; queda a criterio del caller.
        """
        result = await self.db.execute(
            select(Checklist.id).where(Checklist.orden_trabajo_id == orden_id)
        )
        existente_id = result.scalar_one_or_none()
        if existente_id:
            return

        tpl_dto = await self.get_template_for_order(orden_id)

        chk = Checklist(orden_trabajo_id=orden_id)
        self.db.add(chk)
        await self.db.flush()

        for paso in tpl_dto.pasos:
            self.db.add(
                ChecklistItem(
                    checklist_id=chk.id,
                    step_number=paso.step_number,
                    titulo=paso.titulo,
                    instrucciones=paso.instrucciones,
                    evidencia_schema=paso.evidencia_schema,
                )
            )

    async def get_checklist(self, orden_id: UUID) -> ChecklistOut:
        """
        Retorna el checklist (y sus items) para una orden. Si no existe, lo inicializa desde plantilla.
        """
        stmt = (
            select(Checklist)
            .where(Checklist.orden_trabajo_id == orden_id)
            .options(selectinload(Checklist.items))
        )
        chk = (await self.db.execute(stmt)).scalars().first()
        if not chk:
            await self.init_checklist(orden_id)
            chk = (await self.db.execute(stmt)).scalars().first()

        chk_items_sorted = sorted(chk.items, key=lambda i: i.step_number)

        items_out = [
            ChecklistItemOut(
                step_number=i.step_number,
                titulo=i.titulo,
                instrucciones=i.instrucciones,
                evidencia_schema=i.evidencia_schema,
                is_completed=i.is_completed,
                evidencia_data=i.evidencia_data or {},
                comentario=i.comentario,
                confirmed_at=i.confirmed_at,
            )
            for i in chk_items_sorted
        ]

        total = len(items_out)
        nums = [itm.step_number for itm in items_out]
        last = max((itm.step_number for itm in items_out if itm.is_completed), default=0)
        current = last + 1 if last < total else total

        return ChecklistOut(
            id=chk.id,
            orden_trabajo_id=chk.orden_trabajo_id,
            hora_entrada=chk.hora_entrada,
            hora_salida=chk.hora_salida,
            observaciones=chk.observaciones,
            firma_tecnico=chk.firma_tecnico,
            firma_cliente=chk.firma_cliente,
            check_metadata=chk.check_metadata or {},
            items=items_out,
            total_steps=total,
            step_numbers=nums,
            current_step=current,
        )

    async def get_checklist_con_items(self, orden_id: UUID):
        """
        Helper para cargar el modelo Checklist con sus items (si existe).
        """
        result = await self.db.execute(
            select(Checklist)
            .where(Checklist.orden_trabajo_id == orden_id)
            .options(selectinload(Checklist.items))
        )
        return result.scalar_one_or_none()

    async def update_item(
        self,
        orden_id: UUID,
        step_number: int,
        evidencia_data: dict = None,
        comentario: str = None,
        confirm: bool = False,
    ) -> ChecklistItemOut:
        """
        Actualiza evidencia/comentario de un item y opcionalmente lo confirma.
        """
        chk_dto = await self.get_checklist(orden_id)
        it_dto = next((i for i in chk_dto.items if i.step_number == step_number), None)
        if not it_dto:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Paso no encontrado")
        if it_dto.is_completed:
            raise HTTPException(status.HTTP_409_CONFLICT, "Paso ya confirmado")

        stmt = select(ChecklistItem).where(
            ChecklistItem.checklist_id == chk_dto.id,
            ChecklistItem.step_number == step_number,
        )
        db_item = (await self.db.execute(stmt)).scalars().first()

        if evidencia_data is not None:
            db_item.evidencia_data = evidencia_data
        if comentario is not None:
            db_item.comentario = comentario
        if confirm:
            db_item.is_completed = True
            db_item.confirmed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_item)

        return ChecklistItemOut.from_orm(db_item)

    # ---------- Sync ----------

    async def sync_full_checklist(self, orden_id: UUID, payload: ChecklistSyncPayload) -> Checklist:
        """
        Sincroniza cabecera + items del checklist desde el payload offline.
        No hace commit; queda a criterio del caller.
        """
        await self.init_checklist(orden_id)

        chk = await self.db.scalar(
            select(Checklist)
            .where(Checklist.orden_trabajo_id == orden_id)
            .options(selectinload(Checklist.items))
        )
        if not chk:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist no encontrado")

        # Cabecera (normalizada a hora Panamá)
        chk.hora_entrada = to_panama_time(payload.hora_entrada)
        chk.hora_salida = to_panama_time(payload.hora_salida)

        if payload.observaciones is not None:
            chk.observaciones = payload.observaciones

        # Merge de metadata (no borra lo existente)
        chk.check_metadata = {**(chk.check_metadata or {}), **(payload.check_metadata or {})}

        # GPS guardado en metadata (resumen)
        if payload.lat is not None and payload.lon is not None:
            md = chk.check_metadata or {}
            md["gps"] = {"lat": float(payload.lat), "lon": float(payload.lon)}
            chk.check_metadata = md

        items_by_step = {it.step_number: it for it in (chk.items or [])}
        now_utc = datetime.utcnow()

        for it_in in payload.items:
            db_item = items_by_step.get(it_in.step_number)
            if not db_item:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    f"Paso {it_in.step_number} no existe en checklist",
                )

            if it_in.evidencia_data is not None:
                db_item.evidencia_data = dict(it_in.evidencia_data or {})
            if it_in.comentario is not None:
                db_item.comentario = it_in.comentario

            if it_in.is_completed:
                if not db_item.is_completed:
                    db_item.is_completed = True
                if db_item.confirmed_at is None:
                    db_item.confirmed_at = now_utc

        await self.db.flush()
        return chk
