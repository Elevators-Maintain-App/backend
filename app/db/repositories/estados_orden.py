from app.db.models.enums.estados_orden import EstadoOrden
from app.schemas.estados_orden import EstadoOrdenCreate, EstadoOrdenUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDEstadoOrden(CRUDBaseRepository[EstadoOrden, EstadoOrdenCreate, EstadoOrdenUpdate]):
    pass

estado_orden_crud = CRUDEstadoOrden(EstadoOrden)