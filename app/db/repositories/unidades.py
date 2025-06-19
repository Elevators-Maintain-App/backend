from app.db.models.unidades import Unidad
from app.schemas.unidades import UnidadCreate, UnidadUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDUnidades(CRUDBaseRepository[Unidad, UnidadCreate, UnidadUpdate]):
    ...

unidad_crud = CRUDUnidades(Unidad)