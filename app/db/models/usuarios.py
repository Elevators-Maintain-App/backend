# app/db/models/usuarios.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
import enum

class Rol(enum.Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "superAdmin"
    SUPERVISOR = "supervisor"
    CLIENT = "client"
    TECHNICIAN = "technician"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uid = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companias.id"), nullable=False)
    document_id = Column(String, nullable=False)
    document_type_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)    
    rol = Column(Enum(Rol), nullable=False)
    nivel = Column(String, nullable=True)
    zona_geografica_id = Column(UUID(as_uuid=True), ForeignKey("zonas_geograficas.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Compania", back_populates="usuarios", foreign_keys=[company_id])
    document_type = relationship("TipoDocumento", back_populates="usuarios", foreign_keys=[document_type_id])
    zona_geografica = relationship("ZonaGeografica", back_populates="usuarios", foreign_keys=[zona_geografica_id])
