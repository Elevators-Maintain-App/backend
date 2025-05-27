# app/db/models/enums/prioridades.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.db.session import Base

class Prioridad(Base):
    __tablename__ = 'prioridades'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
