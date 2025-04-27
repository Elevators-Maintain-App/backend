from app.db.models.evidencias_multimedia import EvidenciaMultimedia
from app.schemas.evidencias_multimedia import EvidenciaMultimediaCreate, EvidenciaMultimediaUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDEvidenciasMultimedia(CRUDBaseRepository[EvidenciaMultimedia, EvidenciaMultimediaCreate, EvidenciaMultimediaUpdate]):
    pass

evidenciamultimedia = CRUDEvidenciasMultimedia(EvidenciaMultimedia)