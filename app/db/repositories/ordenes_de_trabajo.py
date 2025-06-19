from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoCreate, OrdenDeTrabajoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDOrdenesDeTrabajo(CRUDBaseRepository[OrdenDeTrabajo, OrdenDeTrabajoCreate, OrdenDeTrabajoUpdate]):
    ...

orden_de_trabajo_crud = CRUDOrdenesDeTrabajo(OrdenDeTrabajo)