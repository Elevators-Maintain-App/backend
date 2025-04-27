from app.db.models.zonas_geograficas import ZonaGeografica
from app.schemas.zonas_geograficas import ZonaGeograficaCreate, ZonaGeograficaUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDZonasGeograficas(CRUDBaseRepository[ZonaGeografica, ZonaGeograficaCreate, ZonaGeograficaUpdate]):
    pass

zona_geografica_crud = CRUDZonasGeograficas(ZonaGeografica)