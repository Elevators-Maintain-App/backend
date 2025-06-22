from abc import ABC
from app.db.models.usuarios import Usuario
from typing import Optional
from uuid import UUID

class ClienteCaseInterface(ABC):
    def obtener_filtros_para_listar_clientes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        ...

    def obtener_filtro_para_totalizar_clientes(self, usuario_actual: Usuario, company_id: Optional[UUID], tipo_documento_id: Optional[int]) -> dict:
        ...
        
    def puede_ver_cliente(self, usuario_actual: Usuario, cliente_id: str, cliente_company_id: Optional[UUID] = None) -> bool:
        ...
        
    def puede_gestionar_clientes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_crear_clientes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_eliminar_clientes(self, usuario_actual: Usuario) -> bool:
        ... 