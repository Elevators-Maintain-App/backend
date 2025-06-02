import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Compania(Base):
    __tablename__ = 'companias'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    documento = Column(String, nullable=False)
    
    # The document type this company USES (assigned by parent company or system)
    tipo_documento_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=False)
    
    nombre = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship to the document type this company USES
    document_type_in_use = relationship(
        "TipoDocumento",
        back_populates="companies_using_this_type",
        foreign_keys=[tipo_documento_id]
    )
    
    # Relationship to document types this company OWNS/CREATED
    owned_document_types = relationship(
        "TipoDocumento",
        back_populates="owner_compania",
        foreign_keys="TipoDocumento.owner_compania_id",
        cascade="all, delete-orphan"
    )

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