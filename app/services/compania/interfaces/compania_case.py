from abc import ABC
from app.db.models.usuarios import Usuario
from app.auth.firebase import FirebaseUser
from typing import Optional
from uuid import UUID
from app.db.models.usuarios import Rol

class CompaniaCaseInterface(ABC):
    def obtener_filtros_para_listar_companias(self, usuario_actual: Usuario, search: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        ...

    def obtener_filtro_para_totalizar_companias(self, usuario_actual: Usuario, tipo_documento_id: Optional[int]) -> dict:
        ...
        
    def puede_ver_compania(self, usuario_actual: Usuario, compania_id: str) -> bool:
        ...
        
    def puede_gestionar_companias(self, usuario_actual: FirebaseUser) -> bool:
        ...