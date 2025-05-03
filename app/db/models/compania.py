import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Compania(Base):
    __tablename__ = 'companias'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    documento = Column(String, nullable=False)
    tipo_documento_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=False)
    nombre = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    tipo_documento = relationship("TipoDocumento") 