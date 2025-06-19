# app/db/models/clientes.py

import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=True)
    documento = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    ciudad = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    logo = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    tipo_documento_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companias.id'), nullable=False, index=True)
    pais_id = Column(Integer, ForeignKey('paises.id'), nullable=True)

    # Relaciones
    pais = relationship("Pais", back_populates="clientes", foreign_keys=[pais_id])
    compania = relationship("Compania", back_populates="clientes", foreign_keys=[company_id])
    tipos_documento = relationship("TipoDocumento", foreign_keys=[tipo_documento_id])
    ordenes_de_trabajo = relationship("OrdenDeTrabajo", back_populates="cliente", cascade="all, delete-orphan")
    unidades = relationship("Unidad", back_populates="cliente", cascade="all, delete-orphan")
    proyectos = relationship("Proyecto", back_populates="cliente", cascade="all, delete-orphan")

