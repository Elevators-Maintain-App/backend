# app/db/models/tecnicos.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Tecnico(Base):
    __tablename__ = 'tecnicos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=True)
    nivel = Column(String, nullable=True)
    zona_geografica_id = Column(UUID(as_uuid=True), ForeignKey('zonas_geograficas.id'), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    zona_geografica = relationship("ZonaGeografica", back_populates="tecnicos")
    ordenes_de_trabajo = relationship("OrdenDeTrabajo", back_populates="tecnico", cascade="all, delete-orphan")
