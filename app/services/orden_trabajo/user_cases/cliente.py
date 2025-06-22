from app.db.models.usuarios import Usuario
from app.services.orden_trabajo.interfaces import OrdenTrabajoCaseInterface
from typing import Optional
from uuid import UUID

class ClienteOrdenTrabajoCase(OrdenTrabajoCaseInterface):
    def obtener_filtros_para_listar_ordenes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        # Client can only see work orders related to their own projects
        # This would require a more complex query joining through projects
        # For now, we'll use a basic filter that should be enhanced with join logic
        filters = {
            "exact_filters": {
                # This is a simplified approach - in reality we'd need to filter by projects
                # where the client is the owner of the project
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
        # Client can only count work orders related to their projects
        filters = {
            "exact_filters": {
                # This would need to be enhanced with project filtering logic
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
        """Client can only view work orders related to their projects"""
        # This would require checking if the work order belongs to a unit 
        # that belongs to a project owned by this client
        # For now, return True and rely on other filtering
        return True
        
    def puede_gestionar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Client cannot manage work orders"""
        return False
        
    def puede_crear_ordenes(self, usuario_actual: Usuario) -> bool:
        """Client cannot create work orders"""
        return False
        
    def puede_eliminar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Client cannot delete work orders"""
        return False
        
    def puede_asignar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Client cannot assign work orders"""
        return False
        
    def puede_ejecutar_ordenes(self, usuario_actual: Usuario) -> bool:
        """Client cannot execute work orders"""
        return False 