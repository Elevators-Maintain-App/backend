from app.db.models.usuarios import Usuario
from app.services.cliente.interfaces import ClienteCaseInterface
from typing import Optional
from uuid import UUID

class ClienteClienteCase(ClienteCaseInterface):
    def obtener_filtros_para_listar_clientes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        # Client can only see themselves (this should be very restrictive)
        # In most cases, clients shouldn't be listing other clients
        filters = {
            "exact_filters": {
                "id": usuario_actual.id,  # Only themselves
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        return filters
    
    def obtener_filtro_para_totalizar_clientes(self, usuario_actual: Usuario, company_id: Optional[UUID], tipo_documento_id: Optional[int]) -> dict:
        # Client can only count themselves (result should be 1 or 0)
        filters = {
            "exact_filters": {
                "id": usuario_actual.id,  # Only themselves
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        return filters
        
    def puede_ver_cliente(self, usuario_actual: Usuario, cliente_id: str, cliente_company_id: Optional[UUID] = None) -> bool:
        """Client can only view their own information"""
        return str(usuario_actual.id) == cliente_id
        
    def puede_gestionar_clientes(self, usuario_actual: Usuario) -> bool:
        """Client cannot manage other clients"""
        return False
        
    def puede_crear_clientes(self, usuario_actual: Usuario) -> bool:
        """Client cannot create other clients"""
        return False
        
    def puede_eliminar_clientes(self, usuario_actual: Usuario) -> bool:
        """Client cannot delete clients"""
        return False 