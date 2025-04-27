# app/db/models/checklists.py

from sqlalchemy import Column, Integer, String, Text, Time, JSON, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Checklist(Base):
    __tablename__ = 'checklists'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    hora_entrada = Column(Time, nullable=True)
    hora_salida = Column(Time, nullable=True)
    lista_revisiones = Column(JSON, nullable=True)
    observaciones = Column(Text, nullable=True)
    firma_tecnico = Column(String, nullable=True)
    firma_cliente = Column(String, nullable=True)
    orden_trabajo_id = Column(UUID(as_uuid=True), ForeignKey('ordenes_de_trabajo.id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    orden_de_trabajo = relationship("OrdenDeTrabajo", back_populates="checklists")

