from app.db.models.enums.tipos_orden import TipoOrden
from app.schemas.tipos_orden import TipoOrdenCreate, TipoOrdenUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposOrden(CRUDBaseRepository[TipoOrden, TipoOrdenCreate, TipoOrdenUpdate]):
    pass

tipo_orden_crud = CRUDTiposOrden(TipoOrden)