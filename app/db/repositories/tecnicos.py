from app.db.models.tecnicos import Tecnico
from app.schemas.tecnicos import TecnicoCreate, TecnicoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTecnicos(CRUDBaseRepository[Tecnico, TecnicoCreate, TecnicoUpdate]):
    pass

tecnico_crud = CRUDTecnicos(Tecnico)