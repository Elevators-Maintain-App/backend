from app.db.models.enums.pais import Pais
from app.db.repositories.base import CRUDBaseRepository

class PaisRepository(CRUDBaseRepository[Pais, Pais, Pais]):
    def __init__(self):
        super().__init__(Pais)
    ...