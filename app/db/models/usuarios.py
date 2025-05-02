# app/db/models/usuarios.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Usuario(Base):
    __tablename__ = "usuarios"

    uid = Column(String, primary_key=True)  # Firebase UID
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False)  # "tecnico", "supervisor", "admin", etc.
    nivel = Column(String, nullable=True)  # Solo aplica a técnicos
    zona_geografica_id = Column(UUID(as_uuid=True), ForeignKey("zonas_geograficas.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones inversas
    ordenes_asignadas = relationship(
        "OrdenDeTrabajo",
        foreign_keys="OrdenDeTrabajo.tecnico_id",
        back_populates="tecnico"
    )

    ordenes_supervisadas = relationship(
        "OrdenDeTrabajo",
        foreign_keys="OrdenDeTrabajo.supervisor_id",
        back_populates="supervisor"
    )

    zona_geografica = relationship("ZonaGeografica", back_populates="usuarios")
