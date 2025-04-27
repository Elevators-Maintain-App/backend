# app/db/models/evidencias_multimedia.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class EvidenciaMultimedia(Base):
    __tablename__ = 'evidencias_multimedia'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    url = Column(String, nullable=True)
    ubicacion_gps = Column(String, nullable=True)
    fecha_hora = Column(TIMESTAMP, nullable=True)
    tipo_evidencia_id = Column(Integer, ForeignKey('tipos_evidencia.id'), nullable=False)
    orden_trabajo_id = Column(UUID(as_uuid=True), ForeignKey('ordenes_de_trabajo.id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    tipo_evidencia = relationship("TipoEvidencia")
    orden_de_trabajo = relationship("OrdenDeTrabajo", back_populates="evidencias_multimedia")
