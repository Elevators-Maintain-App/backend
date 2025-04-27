# app/db/models/hojas_de_vida.py

from sqlalchemy import Column, Integer, JSON, Date, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class HojaDeVida(Base):
    __tablename__ = 'hojas_de_vida'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    historial_trabajos = Column(JSON, nullable=True)
    lista_trabajos_programados = Column(JSON, nullable=True)
    fecha_proximo_mantenimiento = Column(Date, nullable=True)
    unidad_id = Column(UUID(as_uuid=True), ForeignKey('unidades.id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    unidad = relationship("Unidad", back_populates="hoja_de_vida")
