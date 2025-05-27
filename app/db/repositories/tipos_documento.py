from app.db.models.enums.tipos_documento import TipoDocumento
from app.schemas.tipos_documento import TipoDocumentoCreate, TipoDocumentoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposDocumento(CRUDBaseRepository[TipoDocumento, TipoDocumentoCreate, TipoDocumentoUpdate]):
    pass

tipo_documento_crud = CRUDTiposDocumento(TipoDocumento)