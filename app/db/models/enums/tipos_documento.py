# app/db/models/enums/tipos_documento.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.db.session import Base

class TipoDocumento(Base):
    __tablename__ = 'tipos_documento'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
