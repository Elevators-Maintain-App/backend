from abc import ABC
from app.db.models.usuarios import Usuario
from typing import Optional
from uuid import UUID

class OrdenTrabajoCaseInterface(ABC):
    def obtener_filtros_para_listar_ordenes(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        ...

    def obtener_filtro_para_totalizar_ordenes(self, usuario_actual: Usuario, company_id: Optional[UUID], estado_id: Optional[int], tipo_orden_id: Optional[int], prioridad_id: Optional[int]) -> dict:
        ...
        
    def puede_ver_orden(self, usuario_actual: Usuario, orden_id: str, orden_company_id: Optional[UUID] = None, supervisor_id: Optional[str] = None, tecnico_id: Optional[str] = None) -> bool:
        ...
        
    def puede_gestionar_ordenes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_crear_ordenes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_eliminar_ordenes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_asignar_ordenes(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_ejecutar_ordenes(self, usuario_actual: Usuario) -> bool:
        ... 