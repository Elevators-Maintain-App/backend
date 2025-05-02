# app/db/models/ordenes_de_trabajo.py

from sqlalchemy import Column, Integer, Text, DECIMAL, Date, TIMESTAMP, ForeignKey, func, String
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class OrdenDeTrabajo(Base):
    __tablename__ = 'ordenes_de_trabajo'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    descripcion = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    valor = Column(DECIMAL, nullable=True)
    fecha = Column(Date, nullable=True)
    tipo_orden_id = Column(Integer, ForeignKey('tipos_orden.id'), nullable=False)
    estado_id = Column(Integer, ForeignKey('estados_orden.id'), nullable=False)
    prioridad_id = Column(Integer, ForeignKey('prioridades.id'), nullable=False)
    supervisor_id = Column(String, ForeignKey("usuarios.uid"), nullable=False)
    tecnico_id = Column(String, ForeignKey("usuarios.uid"), nullable=False)
    unidad_id = Column(UUID(as_uuid=True), ForeignKey('unidades.id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    tipo_orden = relationship("TipoOrden")
    estado = relationship("EstadoOrden")
    prioridad = relationship("Prioridad")
    unidad = relationship("Unidad", back_populates="ordenes_de_trabajo")
    checklists = relationship("Checklist", back_populates="orden_de_trabajo", cascade="all, delete-orphan")
    evidencias_multimedia = relationship("EvidenciaMultimedia", back_populates="orden_de_trabajo", cascade="all, delete-orphan")
    supervisor = relationship("Usuario", foreign_keys=[supervisor_id], back_populates="ordenes_supervisadas")
    tecnico = relationship("Usuario", foreign_keys=[tecnico_id], back_populates="ordenes_asignadas")
