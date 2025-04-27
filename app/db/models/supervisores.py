# app/db/models/supervisores.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Supervisor(Base):
    __tablename__ = 'supervisores'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    ordenes_de_trabajo = relationship("OrdenDeTrabajo", back_populates="supervisor", cascade="all, delete-orphan")
