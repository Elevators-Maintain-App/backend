from app.db.models.enums.prioridades import Prioridad
from app.schemas.prioridades import PrioridadCreate, PrioridadUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDPrioridades(CRUDBaseRepository[Prioridad, PrioridadCreate, PrioridadUpdate]):
    pass

prioridad_crud = CRUDPrioridades(Prioridad)