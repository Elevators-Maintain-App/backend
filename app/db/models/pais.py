import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.db.session import Base

class Pais(Base):
    __tablename__ = "paises"

    id       = sa.Column(sa.Integer, primary_key=True)
    alpha_2  = sa.Column(sa.String(2),  unique=True)
    alpha_3  = sa.Column(sa.String(3),  unique=True)
    nombre   = sa.Column(sa.String,     nullable=False)

    companias = relationship("Compania", back_populates="pais")