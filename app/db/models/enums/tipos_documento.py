# app/db/models/enums/tipos_documento.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class TipoDocumento(Base):
    __tablename__ = 'tipos_documento'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    
    # Company that OWNS/CREATED this document type (nullable for system-wide types)
    owner_compania_id = Column(UUID(as_uuid=True), ForeignKey('companias.id'), nullable=True)
    
    # Flag to indicate if it's a system-wide type or company-specific
    is_system_wide = Column(Boolean, default=False, nullable=True)
    
    # Audit fields
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationship to the company that OWNS this document type
    owner_compania = relationship(
        "Compania",
        back_populates="owned_document_types",
        foreign_keys=[owner_compania_id]
    )
    
    # Relationship to companies that USE this document type
    companies_using_this_type = relationship(
        "Compania",
        back_populates="document_type_in_use",
        foreign_keys="Compania.tipo_documento_id"
    )

    usuarios = relationship("Usuario", back_populates="document_type")
