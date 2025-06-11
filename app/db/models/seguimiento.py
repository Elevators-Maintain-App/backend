# app/db/models/seguimiento.py
import uuid, enum
from sqlalchemy import Column, Enum, Float, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class EventoOrden(str, enum.Enum):
    INICIO = "INICIO"
    PAUSA = "PAUSA"
    REANUDACION = "REANUDACION"
    FIN = "FIN"
    PASO_COMPLETADO = "PASO_COMPLETADO"   # ← nuevo

class OrdenTrabajoSeguimiento(Base):
    __tablename__ = "ordenes_trabajo_seguimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orden_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_de_trabajo.id"), nullable=False)
    # opcional si quieres guardar qué paso se completó
    checklist_item_id = Column(UUID(as_uuid=True), ForeignKey("checklist_items.id"), nullable=True)

    evento = Column(Enum(EventoOrden, name="evento_orden"), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())

    orden = relationship("OrdenDeTrabajo", back_populates="seguimientos")
    checklist_item = relationship("ChecklistItem", back_populates="seguimientos", lazy="joined")
