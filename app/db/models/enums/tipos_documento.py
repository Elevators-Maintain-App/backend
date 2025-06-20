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
        
    # Audit fields
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    companias = relationship("Compania", back_populates="document_type")
    usuarios = relationship("Usuario", back_populates="document_type")
