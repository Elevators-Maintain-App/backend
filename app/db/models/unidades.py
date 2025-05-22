# app/db/models/unidades.py

from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Unidad(Base):
    __tablename__ = 'unidades'

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    kpi_funcionamiento = Column(String, nullable=True)
    proyecto_id        = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), nullable=False)
    tipo_unidad_id     = Column(Integer, ForeignKey('tipos_unidad.id'), nullable=False)
    company_id         = Column(UUID(as_uuid=True), ForeignKey('companias.id'), nullable=False, index=True)
    created_at         = Column(TIMESTAMP, server_default=func.now())
    updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    proyecto           = relationship("Proyecto", back_populates="unidades")
    tipo_unidad        = relationship("TipoUnidad")
    compania           = relationship("Compania", back_populates="unidades")
    hoja_de_vida       = relationship("HojaDeVida", back_populates="unidad", uselist=False, cascade="all, delete-orphan")
    ordenes_de_trabajo = relationship("OrdenDeTrabajo", back_populates="unidad", cascade="all, delete-orphan")
