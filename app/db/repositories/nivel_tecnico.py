from app.db.models.nivel_tecnico import NivelTecnico
from app.db.repositories.base import CRUDBaseRepository

class CRUDNivelTecnico(CRUDBaseRepository[NivelTecnico]):
    pass

nivel_tecnico_crud = CRUDNivelTecnico(NivelTecnico)