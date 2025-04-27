# app/db/models/zonas_geograficas.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class ZonaGeografica(Base):
    __tablename__ = 'zonas_geograficas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    proyectos = relationship("Proyecto", back_populates="zona_geografica", cascade="all, delete-orphan")
    tecnicos = relationship("Tecnico", back_populates="zona_geografica", cascade="all, delete-orphan")
