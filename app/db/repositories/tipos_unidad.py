from app.db.models.enums.tipos_unidad import TipoUnidad
from app.schemas.tipos_unidad import TipoUnidadCreate, TipoUnidadUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposUnidad(CRUDBaseRepository[TipoUnidad, TipoUnidadCreate, TipoUnidadUpdate]):
    pass

tipo_unidad_crud = CRUDTiposUnidad(TipoUnidad)