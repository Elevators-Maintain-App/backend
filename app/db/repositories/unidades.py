from app.db.models.unidades import Unidad
from app.schemas.unidades import UnidadCreate, UnidadUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDUnidades(CRUDBaseRepository[Unidad, UnidadCreate, UnidadUpdate]):
    pass

unidad_crud = CRUDUnidades(Unidad)