from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models.enums.tipos_documento import TipoDocumento
from app.schemas.tipos_documento import TipoDocumentoCreate, TipoDocumentoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposDocumento(CRUDBaseRepository[TipoDocumento, TipoDocumentoCreate, TipoDocumentoUpdate]):
    ...    

tipo_documento_crud = CRUDTiposDocumento(TipoDocumento)