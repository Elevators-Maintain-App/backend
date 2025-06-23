from app.db.models.usuarios import Usuario
from app.services.unidad.interfaces import UnidadCaseInterface
from typing import Optional
from uuid import UUID

class SupervisorUnidadCase(UnidadCaseInterface):
    def obtener_filtros_para_listar_unidades(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], proyecto_id: Optional[str], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        # Supervisor can see units from their own company
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
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
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters
    
    def obtener_filtro_para_totalizar_unidades(self, usuario_actual: Usuario, company_id: Optional[UUID], proyecto_id: Optional[UUID], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        # Supervisor can count units from their own company
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if proyecto_id:
            filters["exact_filters"]["proyecto_id"] = proyecto_id
        if tipo_unidad_id:
            filters["exact_filters"]["tipo_unidad_id"] = tipo_unidad_id
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters
        
    def puede_ver_unidad(self, usuario_actual: Usuario, unidad_id: str, unidad_company_id: Optional[UUID] = None, proyecto_id: Optional[UUID] = None, cliente_id: Optional[str] = None) -> bool:
        """Supervisor can view units from their own company"""
        if unidad_company_id:
            return usuario_actual.company_id == unidad_company_id
        return True  # Will be filtered by other methods
        
    def puede_gestionar_unidades(self, usuario_actual: Usuario) -> bool:
        """Supervisor can manage units in their company"""
        return True
        
    def puede_crear_unidades(self, usuario_actual: Usuario) -> bool:
        """Supervisor can create units in their company"""
        return True
        
    def puede_eliminar_unidades(self, usuario_actual: Usuario) -> bool:
        """Supervisor cannot delete units (business rule)"""
        return False
        
    def puede_realizar_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Supervisor doesn't perform maintenance directly but supervises it"""
        return False
        
    def puede_ver_historial_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Supervisor can view maintenance history to validate work"""
        return True 