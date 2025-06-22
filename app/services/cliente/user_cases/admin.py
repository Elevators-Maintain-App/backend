from app.db.models.usuarios import Usuario
from app.services.cliente.interfaces import ClienteCaseInterface
from typing import Optional
from uuid import UUID

class AdminClienteCase(ClienteCaseInterface):
    def obtener_filtros_para_listar_clientes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        # Admin can only see clients from their own company
        filters = {
            "exact_filters": {
                "compania_id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
    
    def obtener_filtro_para_totalizar_clientes(self, usuario_actual: Usuario, company_id: Optional[UUID], tipo_documento_id: Optional[int]) -> dict:
        # Admin can only count clients from their own company
        filters = {
            "exact_filters": {
                "compania_id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
        
    def puede_ver_cliente(self, usuario_actual: Usuario, cliente_id: str, cliente_company_id: Optional[UUID] = None) -> bool:
        """Admin can only view clients from their own company"""
        if cliente_company_id:
            return usuario_actual.company_id == cliente_company_id
        return True  # Will be filtered by other methods
        
    def puede_gestionar_clientes(self, usuario_actual: Usuario) -> bool:
        """Admin can manage clients in their company"""
        return True
        
    def puede_crear_clientes(self, usuario_actual: Usuario) -> bool:
        """Admin can create clients in their company"""
        return True
        
    def puede_eliminar_clientes(self, usuario_actual: Usuario) -> bool:
        """Admin can delete clients in their company"""
        return True 