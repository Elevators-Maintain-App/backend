from app.db.models.usuarios import Usuario
from app.services.cliente.interfaces import ClienteCaseInterface
from typing import Optional
from uuid import UUID

class SuperAdminClienteCase(ClienteCaseInterface):
    def obtener_filtros_para_listar_clientes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if company_id:
            filters["exact_filters"]["compania_id"] = UUID(company_id)
        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
    
    def obtener_filtro_para_totalizar_clientes(self, usuario_actual: Usuario, company_id: Optional[UUID], tipo_documento_id: Optional[int]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }

        if company_id:
            filters["exact_filters"]["compania_id"] = company_id
        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
        
    def puede_ver_cliente(self, usuario_actual: Usuario, cliente_id: str, cliente_company_id: Optional[UUID] = None) -> bool:
        """SuperAdmin can view any client"""
        return True
        
    def puede_gestionar_clientes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can manage all clients"""
        return True
        
    def puede_crear_clientes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can create clients"""
        return True
        
    def puede_eliminar_clientes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can delete clients"""
        return True 