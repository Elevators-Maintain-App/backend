# # # app/services/checklists.py

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import selectinload

from app.db.models.checklists import (
    ChecklistTemplate,
    Checklist, ChecklistItem, ChecklistItemTemplate
)
from app.db.models.unidades import Unidad
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.schemas.checklists import (
    ChecklistTemplateOut, ChecklistTemplateOut2, ChecklistItemOut, ChecklistOut, ChecklistTemplateCreate, ChecklistItemTemplateOut
)

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
        # Verificar si ya existe un checklist para esta orden
        result = await self.db.execute(
            select(Checklist).where(Checklist.orden_trabajo_id == orden_id)
        )
        existente = result.scalars().first()
        if existente:
            return  # ya existe, no hacer nada

        # Obtener plantilla
        tpl_dto = await self.get_template_for_order(orden_id)

        # Crear checklist
        chk = Checklist(orden_trabajo_id=orden_id)
        self.db.add(chk)
        await self.db.flush()

        # Crear ítems
        for paso in tpl_dto.pasos:
            item = ChecklistItem(
                checklist_id=chk.id,
                step_number=paso.step_number,
                titulo=paso.titulo,
                instrucciones=paso.instrucciones,
                evidencia_schema=paso.evidencia_schema
            )
            self.db.add(item)

        await self.db.commit()

    async def get_checklist(self, orden_id: UUID) -> ChecklistOut:
        # 1) Cargar o inicializar checklist
        stmt = (
            select(Checklist)
            .where(Checklist.orden_trabajo_id == orden_id)
            .options(selectinload(Checklist.items))
        )
        chk = (await self.db.execute(stmt)).scalars().first()
        if not chk:
            chk = await self.init_checklist(orden_id)

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