from app.db.models.usuarios import Usuario
from app.services.orden_trabajo.interfaces import OrdenTrabajoCaseInterface
from typing import Optional
from uuid import UUID

class SuperAdminOrdenTrabajoCase(OrdenTrabajoCaseInterface):
    def obtener_filtros_para_listar_ordenes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["descripcion"] = f"%{search}%"
        if company_id:
            filters["exact_filters"]["company_id"] = UUID(company_id)
        if estado_id:
            filters["exact_filters"]["estado_id"] = estado_id
        if tipo_orden_id:
            filters["exact_filters"]["tipo_orden_id"] = tipo_orden_id
        if prioridad_id:
            filters["exact_filters"]["prioridad_id"] = prioridad_id

        return filters
    
    def obtener_filtro_para_totalizar_ordenes(self, usuario_actual: Usuario, company_id: Optional[UUID], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }

        if company_id:
            filters["exact_filters"]["company_id"] = company_id
        if estado_id:
            filters["exact_filters"]["estado_id"] = estado_id
        if tipo_orden_id:
            filters["exact_filters"]["tipo_orden_id"] = tipo_orden_id
        if prioridad_id:
            filters["exact_filters"]["prioridad_id"] = prioridad_id

        return filters
        
    def puede_ver_orden(self, usuario_actual: Usuario, orden_id: str, orden_company_id: Optional[UUID] = None, supervisor_id: Optional[str] = None, tecnico_id: Optional[str] = None) -> bool:
        """SuperAdmin can view any work order"""
        return True
        
    def puede_gestionar_ordenes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can manage all work orders"""
        return True
        
    def puede_crear_ordenes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can create work orders"""
        return True
        
    def puede_eliminar_ordenes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can delete work orders"""
        return True
        
    def puede_asignar_ordenes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can assign work orders"""
        return True
        
    def puede_ejecutar_ordenes(self, usuario_actual: Usuario) -> bool:
        """SuperAdmin can execute work orders"""
        return True 