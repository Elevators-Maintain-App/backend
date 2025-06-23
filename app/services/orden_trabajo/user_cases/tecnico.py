from app.db.models.usuarios import Usuario
from app.services.orden_trabajo.interfaces import OrdenTrabajoCaseInterface
from typing import Optional
from uuid import UUID

class TecnicoOrdenTrabajoCase(OrdenTrabajoCaseInterface):
    def obtener_filtros_para_listar_ordenes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        # Technician can only see work orders assigned to them in their company
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
                "tecnico_id": str(usuario_actual.id),  # Only orders assigned to them
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["descripcion"] = f"%{search}%"
        if estado_id:
            filters["exact_filters"]["estado_id"] = estado_id
        if tipo_orden_id:
            filters["exact_filters"]["tipo_orden_id"] = tipo_orden_id
        if prioridad_id:
            filters["exact_filters"]["prioridad_id"] = prioridad_id

        return filters
    
    def obtener_filtro_para_totalizar_ordenes(self, usuario_actual: Usuario, company_id: Optional[UUID], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        # Technician can only count work orders assigned to them
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
                "tecnico_id": str(usuario_actual.id),  # Only orders assigned to them
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if estado_id:
            filters["exact_filters"]["estado_id"] = estado_id
        if tipo_orden_id:
            filters["exact_filters"]["tipo_orden_id"] = tipo_orden_id
        if prioridad_id:
            filters["exact_filters"]["prioridad_id"] = prioridad_id

        return filters
        
    def puede_ver_orden(self, usuario_actual: Usuario, orden_id: str, orden_company_id: Optional[UUID] = None, supervisor_id: Optional[str] = None, tecnico_id: Optional[str] = None) -> bool:
        """Technician can only view work orders assigned to them in their company"""
        if orden_company_id and tecnico_id:
            return (usuario_actual.company_id == orden_company_id and 
                    str(usuario_actual.id) == tecnico_id)
        return True  # Will be filtered by other methods
        
    def puede_gestionar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Technician has limited management - can update status and add notes"""
        return True
        
    def puede_crear_ordenes(self, usuario_actual: Usuario) -> bool:
        """Technician cannot create work orders"""
        return False
        
    def puede_eliminar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Technician cannot delete work orders"""
        return False
        
    def puede_asignar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Technician cannot assign work orders"""
        return False
        
    def puede_ejecutar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Technician executes work orders (core responsibility)"""
        return True 