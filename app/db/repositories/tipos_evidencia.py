from app.db.models.enums.tipos_evidencia import TipoEvidencia
from app.schemas.tipos_evidencia import TipoEvidenciaCreate, TipoEvidenciaUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposEvidencia(CRUDBaseRepository[TipoEvidencia, TipoEvidenciaCreate, TipoEvidenciaUpdate]):
    pass

tipo_evidencia_crud = CRUDTiposEvidencia(TipoEvidencia)