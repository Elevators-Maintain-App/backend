from app.db.models.nivel_tecnico import NivelTecnico
from app.db.repositories.base import CRUDBaseRepository
from app.schemas.nivel_tecnico_schema import NivelTecnicoCreate, NivelTecnicoUpdate

class CRUDNivelTecnico(CRUDBaseRepository[NivelTecnico, NivelTecnicoCreate, NivelTecnicoUpdate]):
    pass

nivel_tecnico_crud = CRUDNivelTecnico(NivelTecnico)