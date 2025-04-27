# app/db/models/enums/tipos_unidad.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.db.session import Base

class TipoUnidad(Base):
    __tablename__ = 'tipos_unidad'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
