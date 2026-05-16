#app/db/models/compania.py 

import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Compania(Base):
    __tablename__ = 'companias'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=True)
    tipo_documento_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=False)
    documento = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    pais_id = Column(Integer, ForeignKey("paises.id"), nullable=True)
    ciudad = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    logo = Column(String, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())    
    
    # Other existing relationships
    ordenes_de_trabajo = relationship(
        "OrdenDeTrabajo",
        back_populates="compania",
        cascade="all, delete-orphan"
    )

    proyectos = relationship(
        "Proyecto",
        back_populates="compania",
        cascade="all, delete-orphan"
    )

    unidades = relationship(
        "Unidad",
        back_populates="compania",
        cascade="all, delete-orphan"
    )

    niveles_tecnicos = relationship(
        "NivelTecnico",
        back_populates="compania",
        cascade="all, delete-orphan"
    )

    pais = relationship("Pais", back_populates="companias", foreign_keys=[pais_id])

    clientes = relationship("Cliente", back_populates="compania")

    usuarios = relationship("Usuario", back_populates="company", cascade="all, delete-orphan")

    subscriptions = relationship(
        "CompanySubscription",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    usage_periods = relationship(
        "CompanyUsage",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    document_type = relationship("TipoDocumento", back_populates="companias", foreign_keys=[tipo_documento_id])
    
    def __str__(self):
        return f"Compania(id={self.id}, nombre='{self.nombre}', documento='{self.documento}')"
    
    def __repr__(self):
        return self.__str__()
