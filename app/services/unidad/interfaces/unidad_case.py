from abc import ABC
from app.db.models.usuarios import Usuario
from typing import Optional
from uuid import UUID

class UnidadCaseInterface(ABC):
    def obtener_filtros_para_listar_unidades(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], proyecto_id: Optional[str], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        ...

    def obtener_filtro_para_totalizar_unidades(self, usuario_actual: Usuario, company_id: Optional[UUID], proyecto_id: Optional[UUID], tipo_unidad_id: Optional[int], cliente_id: Optional[str]) -> dict:
        ...
        
    def puede_ver_unidad(self, usuario_actual: Usuario, unidad_id: str, unidad_company_id: Optional[UUID] = None, proyecto_id: Optional[UUID] = None, cliente_id: Optional[str] = None) -> bool:
        ...
        
    def puede_gestionar_unidades(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_crear_unidades(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_eliminar_unidades(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_realizar_mantenimiento(self, usuario_actual: Usuario) -> bool:
        ...
        
    def puede_ver_historial_mantenimiento(self, usuario_actual: Usuario) -> bool:
        ... 