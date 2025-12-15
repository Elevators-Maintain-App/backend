# # # app/services/checklists.py

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from datetime import datetime, time
from sqlalchemy.orm import selectinload
from zoneinfo import ZoneInfo
from datetime import timezone

LOCAL_TZ = ZoneInfo("America/Panama")

from app.db.models.checklists import (
    ChecklistTemplate,
    Checklist, ChecklistItem, ChecklistItemTemplate
)
from app.db.models.unidades import Unidad
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.schemas.checklists import (
    ChecklistTemplateOut, ChecklistTemplateOut2, ChecklistItemOut, ChecklistOut, ChecklistTemplateCreate, ChecklistItemTemplateOut
)
from app.schemas.checklists_sync import ChecklistSyncPayload

import logging
logger = logging.getLogger("sync_checklist")

class ChecklistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_template_for_order(self, orden_id: UUID) -> ChecklistTemplateOut:
        # 1) Traer orden y unidad
        orden = await self.db.get(OrdenDeTrabajo, orden_id)
        if not orden:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
        unidad = await self.db.get(Unidad, orden.unidad_id)
        if not unidad:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidad no encontrada")

        # 2) Cargar plantilla con pasos
        stmt = (
            select(ChecklistTemplate)
            .where(
                ChecklistTemplate.tipo_orden_id  == orden.tipo_orden_id,
                ChecklistTemplate.tipo_unidad_id == unidad.tipo_unidad_id
            )
            .options(selectinload(ChecklistTemplate.pasos))
        )
        tpl = (await self.db.execute(stmt)).scalars().first()
        if not tpl:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay plantilla para esta combinación")

        # 3) Convertir pasos a DTO
        pasos_out = [
            ChecklistItemTemplateOut(
                step_number=p.step_number,
                titulo=p.titulo,
                instrucciones=p.instrucciones,
                evidencia_schema=p.evidencia_schema
            )
            for p in tpl.pasos
        ]
        total = len(pasos_out)
        step_nums = [p.step_number for p in pasos_out]
        paso_ids  = [p.id for p in tpl.pasos]

        # 4) Construir y devolver el DTO completo
        return ChecklistTemplateOut(
            id=tpl.id,
            nombre=tpl.nombre,
            tipo_orden_id=tpl.tipo_orden_id,
            tipo_unidad_id=tpl.tipo_unidad_id,
            pasos=pasos_out,
            total_steps=total,
            step_numbers=step_nums,
            pasos_ids=paso_ids,
            current_step=1
        )

    async def init_checklist(self, orden_id: UUID) -> None:
        result = await self.db.execute(
            select(Checklist.id).where(Checklist.orden_trabajo_id == orden_id)
        )
        existente_id = result.scalar_one_or_none()

        logger.info("INIT_CHECKLIST: orden_id=%s exists=%s", str(orden_id), bool(existente_id))
        if existente_id:
            return

        # Obtener plantilla
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

        # NO commit aquí
        logger.info("INIT_CHECKLIST: created checklist_id=%s for orden_id=%s", str(chk.id), str(orden_id))

    async def get_checklist(self, orden_id: UUID) -> ChecklistOut:
        # 1) Cargar o inicializar checklist
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
        # 2) Mapear cada item a su DTO
        items_out = []
        for i in chk_items_sorted:
            items_out.append(ChecklistItemOut(
                step_number     = i.step_number,
                titulo          = i.titulo,
                instrucciones   = i.instrucciones,
                evidencia_schema= i.evidencia_schema,
                is_completed    = i.is_completed,
                evidencia_data  = i.evidencia_data or {},
                comentario      = i.comentario,
                confirmed_at    = i.confirmed_at
            ))

        # 3) Calcular métricas del stepper
        total = len(items_out)
        nums  = [itm.step_number for itm in items_out]
        last = max((itm.step_number for itm in items_out if itm.is_completed), default=0)
        current = last + 1 if last < total else total

        # 4) Construir y devolver el DTO completo
        return ChecklistOut(
            id               = chk.id,
            orden_trabajo_id = chk.orden_trabajo_id,
            hora_entrada     = chk.hora_entrada,
            hora_salida      = chk.hora_salida,
            observaciones    = chk.observaciones,
            firma_tecnico    = chk.firma_tecnico,
            firma_cliente    = chk.firma_cliente,
            check_metadata   = chk.check_metadata or {},
            items            = items_out,
            total_steps      = total,
            step_numbers     = nums,
            current_step     = current
        )

    async def update_item(
        self,
        orden_id: UUID,
        step_number: int,
        evidencia_data: dict = None,
        comentario: str = None,
        confirm: bool = False
    ) -> ChecklistItemOut:
        # 1) Obtener checklist y DTO de ítems
        chk_dto = await self.get_checklist(orden_id)
        it_dto = next((i for i in chk_dto.items if i.step_number == step_number), None)
        if not it_dto:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Paso no encontrado")
        if it_dto.is_completed:
            raise HTTPException(status.HTTP_409_CONFLICT, "Paso ya confirmado")

        # 2) Cargar el item real
        stmt = (
            select(ChecklistItem)
            .where(
                ChecklistItem.checklist_id == chk_dto.id,
                ChecklistItem.step_number  == step_number
            )
        )
        db_item = (await self.db.execute(stmt)).scalars().first()

        # 3) Aplicar cambios
        if evidencia_data is not None:
            db_item.evidencia_data = evidencia_data
        if comentario is not None:
            db_item.comentario = comentario
        if confirm:
            db_item.is_completed = True
            db_item.confirmed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_item)

        # 4) Devolver DTO actualizado
        return ChecklistItemOut.from_orm(db_item)

    async def create_template_with_items(
        self,
        payload: ChecklistTemplateCreate
    ) -> ChecklistTemplate:
        # 1) Validar unicidad de combinación
        exists = await self.db.execute(
            select(ChecklistTemplate)
            .where(
                ChecklistTemplate.tipo_orden_id  == payload.tipo_orden_id,
                ChecklistTemplate.tipo_unidad_id == payload.tipo_unidad_id
            )
        )
        if exists.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una plantilla para esa combinación"
            )

        # 2) Crear la plantilla
        template = ChecklistTemplate(
            nombre=payload.nombre,
            tipo_orden_id=payload.tipo_orden_id,
            tipo_unidad_id=payload.tipo_unidad_id
        )
        self.db.add(template)
        await self.db.flush()  # para obtener template.id

        # 3) Crear cada paso
        pasos_ids = []
        for paso_in in payload.pasos:  # tipo ChecklistItemTemplateCreate
            paso = ChecklistItemTemplate(
                checklist_template_id=template.id,
                step_number=paso_in.step_number,
                titulo=paso_in.titulo,
                instrucciones=paso_in.instrucciones,
                evidencia_schema=paso_in.evidencia_schema
            )
            self.db.add(paso)
            pasos_ids.append(paso.id)

        # 4) Commit y refresh
        await self.db.commit()
        await self.db.refresh(template)
        await self.db.execute(
            select(ChecklistTemplate)
            .options(selectinload(ChecklistTemplate.pasos))
            .where(ChecklistTemplate.id == template.id)
        )
        # ahora template.pasos ya tiene sus IDs
        pasos_ids = [paso.id for paso in template.pasos]

        
        # 5) Preparamos la salida
        return ChecklistTemplateOut2(
            id=template.id,
            nombre=template.nombre,
            tipo_orden_id=template.tipo_orden_id,
            tipo_unidad_id=template.tipo_unidad_id,
            created_at=template.created_at,
            updated_at=template.updated_at,
            pasos_ids=pasos_ids
        )
    

    async def get_checklist_con_items(self, orden_id: UUID):
        from app.db.models.checklists import Checklist
        result = await self.db.execute(
            select(Checklist).where(Checklist.orden_trabajo_id == orden_id).options(selectinload(Checklist.items))
        )
        return result.scalar_one_or_none()
    
    async def sync_full_checklist(self, orden_id: UUID, payload: ChecklistSyncPayload) -> Checklist:
        # Garantizar que exista el checklist (si no, lo crea desde plantilla)
        await self.init_checklist(orden_id)

        chk = await self.db.scalar(
            select(Checklist)
            .where(Checklist.orden_trabajo_id == orden_id)
            .options(selectinload(Checklist.items))
        )
        if not chk:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist no encontrado")

        # Cabecera
        if payload.hora_entrada is not None:
            chk.hora_entrada = payload.hora_entrada if isinstance(payload.hora_entrada, time) else payload.hora_entrada

        if payload.hora_salida is not None:
            if isinstance(payload.hora_salida, datetime):
                dt = payload.hora_salida
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_pa = dt.astimezone(LOCAL_TZ)
                chk.hora_salida = dt_pa.time()
            elif isinstance(payload.hora_salida, time):
                chk.hora_salida = payload.hora_salida

        if payload.observaciones is not None:
            chk.observaciones = payload.observaciones

        # Merge de metadata (no borra lo existente)
        chk.check_metadata = {**(chk.check_metadata or {}), **(payload.check_metadata or {})}

        # GPS único (inicio/ejecución) guardado en metadata
        if payload.lat is not None and payload.lon is not None:
            md = chk.check_metadata or {}
            md["gps"] = {"lat": float(payload.lat), "lon": float(payload.lon)}
            chk.check_metadata = md

        items_by_step = {it.step_number: it for it in (chk.items or [])}
        now_utc = datetime.utcnow()

        for it_in in payload.items:
            db_item = items_by_step.get(it_in.step_number)
            if not db_item:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"Paso {it_in.step_number} no existe en checklist")

            if it_in.evidencia_data is not None:
                db_item.evidencia_data = dict(it_in.evidencia_data or {})
            if it_in.comentario is not None:
                db_item.comentario = it_in.comentario

            if it_in.is_completed:
                if not db_item.is_completed:
                    db_item.is_completed = True
                if db_item.confirmed_at is None:
                    db_item.confirmed_at = now_utc
        


        # loguea 2 pasos actualizados
        count = 0
        for it_in in payload.items:
            db_item = items_by_step.get(it_in.step_number)
            if db_item and count < 3:
                logger.info(
                    "SYNC_FULL: step=%s -> db_completed=%s evidencia_keys=%s comentario_present=%s",
                    db_item.step_number,
                    db_item.is_completed,
                    list((db_item.evidencia_data or {}).keys()),
                    bool(db_item.comentario),
                )
                count += 1

        await self.db.flush()

        # verificación dura: reconsultar 1 item ya flusheado (misma sesión)
        sample_step = payload.items[0].step_number if payload.items else None
        if sample_step:
            verify = await self.db.scalar(
                select(ChecklistItem)
                .where(ChecklistItem.checklist_id == chk.id)
                .where(ChecklistItem.step_number == sample_step)
            )
            logger.info(
                "SYNC_FULL_VERIFY: step=%s evidencia_keys=%s comentario_present=%s",
                sample_step,
                list((verify.evidencia_data or {}).keys()) if verify else None,
                bool(verify.comentario) if verify else None,
            )
        return chk