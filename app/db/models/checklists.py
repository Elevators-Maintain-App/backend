# app/db/models/checklists.py

import uuid
from sqlalchemy import (
    Column, String, Text, Time, JSON, TIMESTAMP, ForeignKey,
    Boolean, Integer, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class ChecklistTemplate(Base):
    __tablename__ = 'checklist_templates'

    id              = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre          = Column(String, nullable=False)
    tipo_orden_id   = Column(Integer, nullable=False)
    tipo_unidad_id  = Column(Integer, nullable=False)
    created_at      = Column(TIMESTAMP, server_default=func.now())
    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    pasos           = relationship(
        "ChecklistItemTemplate",
        back_populates="template",
        cascade="all, delete-orphan"
    )

class ChecklistItemTemplate(Base):
    __tablename__ = 'checklist_item_templates'

    id                     = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    checklist_template_id  = Column(PGUUID(as_uuid=True), ForeignKey('checklist_templates.id'), nullable=False)
    step_number            = Column(Integer, nullable=False)
    titulo                 = Column(String, nullable=False)      
    instrucciones          = Column(Text, nullable=False)
    evidencia_schema       = Column(JSON, nullable=False, default={})
    created_at             = Column(TIMESTAMP, server_default=func.now())
    updated_at             = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    template               = relationship("ChecklistTemplate", back_populates="pasos")

class Checklist(Base):
    __tablename__ = 'checklists'

    id              = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orden_trabajo_id= Column(PGUUID(as_uuid=True), ForeignKey('ordenes_de_trabajo.id'), nullable=False, index=True)
    hora_entrada    = Column(Time, nullable=True)
    hora_salida     = Column(Time, nullable=True)
    observaciones   = Column(Text, nullable=True)
    firma_tecnico   = Column(String, nullable=True)
    firma_cliente   = Column(String, nullable=True)
    check_metadata  = Column(JSON, nullable=True, default={})
    created_at      = Column(TIMESTAMP, server_default=func.now())
    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    reporte_prerevision_url = Column(String, nullable=True)
    reporte_final_url = Column(String, nullable=True)

    items           = relationship(
        "ChecklistItem",
        back_populates="checklist",
        cascade="all, delete-orphan"
    )

    orden_de_trabajo = relationship(
        "OrdenDeTrabajo",
        back_populates="checklists"
    )
    pdf_report_generation_events = relationship(
        "PdfReportGenerationEvent",
        back_populates="checklist",
        passive_deletes=True,
    )

class ChecklistItem(Base):
    __tablename__ = 'checklist_items'

    id              = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    checklist_id    = Column(PGUUID(as_uuid=True), ForeignKey('checklists.id'), nullable=False, index=True)
    step_number     = Column(Integer, nullable=False)
    titulo          = Column(String, nullable=False)   
    instrucciones   = Column(Text, nullable=False) 
    evidencia_schema= Column(JSON, nullable=False, default={})
    is_completed    = Column(Boolean, nullable=False, default=False)
    evidencia_data  = Column(JSON, nullable=True, default={})
    comentario      = Column(Text, nullable=True)
    confirmed_at    = Column(TIMESTAMP, nullable=True)
    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    checklist       = relationship("Checklist", back_populates="items")
    seguimientos = relationship(
        "OrdenTrabajoSeguimiento",
        back_populates="checklist_item",
        cascade="all, delete-orphan"
    )

    __table_args__  = (
        UniqueConstraint('checklist_id', 'step_number', name='ux_checklist_step'),
    )
