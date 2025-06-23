from app.db.models.usuarios import Usuario
from app.services.unidad.interfaces import UnidadCaseInterface
from typing import Optional
from uuid import UUID

class ClienteUnidadCase(UnidadCaseInterface):
    def obtener_filtros_para_listar_unidades(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], proyecto_id: Optional[str], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        # Client can only see units where they are the assigned client
        filters = {
            "exact_filters": {
                "cliente_id": usuario_actual.cliente_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if proyecto_id:
            filters["exact_filters"]["proyecto_id"] = UUID(proyecto_id)
        if tipo_unidad_id:
            filters["exact_filters"]["tipo_unidad_id"] = tipo_unidad_id

        return filters
    
    def obtener_filtro_para_totalizar_unidades(self, usuario_actual: Usuario, company_id: Optional[UUID], proyecto_id: Optional[UUID], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        # Client can only count their own units
        filters = {
            "exact_filters": {
                "cliente_id": usuario_actual.cliente_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if proyecto_id:
            filters["exact_filters"]["proyecto_id"] = proyecto_id
        if tipo_unidad_id:
            filters["exact_filters"]["tipo_unidad_id"] = tipo_unidad_id

        return filters
        
    def puede_ver_unidad(self, usuario_actual: Usuario, unidad_id: str, unidad_company_id: Optional[UUID] = None, proyecto_id: Optional[UUID] = None, cliente_id: Optional[str] = None) -> bool:
        """Client can only view units where they are the assigned client"""
        if cliente_id:
            return usuario_actual.cliente_id == cliente_id
        return True  # Will be filtered by other methods
        
    def puede_gestionar_unidades(self, usuario_actual: Usuario) -> bool:
        """Client cannot manage units"""
        return False
        
    def puede_crear_unidades(self, usuario_actual: Usuario) -> bool:
        """Client cannot create units"""
        return False
        
    def puede_eliminar_unidades(self, usuario_actual: Usuario) -> bool:
        """Client cannot delete units"""
        return False
        
    def puede_realizar_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Client cannot perform maintenance"""
        return False
        
    def puede_ver_historial_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Client can view maintenance history of their elevator units"""
        return True 