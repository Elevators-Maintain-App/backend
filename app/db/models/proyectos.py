# app/db/models/proyectos.py

from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.schemas.proyectos import ProyectoEstado

class Proyecto(Base):
    __tablename__ = 'proyectos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=False)
    direccion = Column(String, nullable=True)
    estado = Column(Enum(ProyectoEstado), nullable=True, default=ProyectoEstado.ACTIVO)
    zona_geografica_id = Column(UUID(as_uuid=True), ForeignKey('zonas_geograficas.id'), nullable=True)
    cliente_id = Column(String, nullable=True)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey('companias.id'),
        nullable=False,
        index=True
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    zona_geografica = relationship("ZonaGeografica", back_populates="proyectos")
    compania = relationship("Compania", back_populates="proyectos")
    unidades = relationship("Unidad", back_populates="proyecto", cascade="all, delete-orphan")
