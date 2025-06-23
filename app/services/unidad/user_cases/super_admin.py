from app.db.models.usuarios import Usuario
from app.services.unidad.interfaces import UnidadCaseInterface
from typing import Optional
from uuid import UUID

class SuperAdminUnidadCase(UnidadCaseInterface):
    def obtener_filtros_para_listar_unidades(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], proyecto_id: Optional[str], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if company_id:
            filters["exact_filters"]["company_id"] = UUID(company_id)
        if proyecto_id:
            filters["exact_filters"]["proyecto_id"] = UUID(proyecto_id)
        if tipo_unidad_id:
            filters["exact_filters"]["tipo_unidad_id"] = tipo_unidad_id
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters
    
    def obtener_filtro_para_totalizar_unidades(self, usuario_actual: Usuario, company_id: Optional[UUID], proyecto_id: Optional[UUID], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }

        if company_id:
            filters["exact_filters"]["company_id"] = company_id
        if proyecto_id:
            filters["exact_filters"]["proyecto_id"] = proyecto_id
        if tipo_unidad_id:
            filters["exact_filters"]["tipo_unidad_id"] = tipo_unidad_id
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters
        
    def puede_ver_unidad(self, usuario_actual: Usuario, unidad_id: str, unidad_company_id: Optional[UUID] = None, proyecto_id: Optional[UUID] = None, cliente_id: Optional[str] = None) -> bool:
        """SuperAdmin can view any unit"""
        return True
        
    def puede_gestionar_unidades(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can manage all units"""
        return True
        
    def puede_crear_unidades(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can create units"""
        return True
        
    def puede_eliminar_unidades(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can delete units"""
        return True
        
    def puede_realizar_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can perform maintenance on any unit"""
        return True
        
    def puede_ver_historial_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can view maintenance history of any unit"""
        return True 