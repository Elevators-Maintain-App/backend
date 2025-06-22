from app.db.models.usuarios import Usuario
from app.services.unidad.interfaces import UnidadCaseInterface
from typing import Optional
from uuid import UUID

class TecnicoUnidadCase(UnidadCaseInterface):
    def obtener_filtros_para_listar_unidades(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], proyecto_id: Optional[str], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        # Technician can see units from their company where they have work orders
        # This requires a more complex query that would join with work orders
        # For now, we'll filter by company and rely on additional business logic
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
        # Technician can count units they work on in their company
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
        """Technician can view units from their company where they have work orders"""
        if unidad_company_id:
            return usuario_actual.company_id == unidad_company_id
        return True  # Additional logic would check for work order assignments
        
    def puede_gestionar_unidades(self, usuario_actual: Usuario) -> bool:
        """Technician has limited management - can update maintenance status"""
        return True
        
    def puede_crear_unidades(self, usuario_actual: Usuario) -> bool:
        """Technician cannot create units"""
        return False
        
    def puede_eliminar_unidades(self, usuario_actual: Usuario) -> bool:
        """Technician cannot delete units"""
        return False
        
    def puede_realizar_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Technician performs maintenance (core responsibility)"""
        return True
        
    def puede_ver_historial_mantenimiento(self, usuario_actual: Usuario) -> bool:
        """Technician can view maintenance history of units they work on"""
        return True 