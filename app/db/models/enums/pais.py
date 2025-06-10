from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.db.session import Base
from sqlalchemy.orm import relationship

class Pais(Base):
    __tablename__ = 'paises'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    alpha_2 = Column(String, nullable=False, unique=True)
    alpha_3 = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Back-reference relationships
    companias = relationship("Compania", back_populates="pais")
    clientes = relationship("Cliente", back_populates="pais")

    