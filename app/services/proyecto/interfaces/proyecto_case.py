from abc import ABC
from app.db.models.usuarios import Usuario
from typing import Optional
from uuid import UUID

class ProyectoCaseInterface(ABC):
    def obtener_filtros_para_listar_proyectos(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], cliente_id: Optional[str]) -> dict:
        ...

    def obtener_filtro_para_totalizar_proyectos(self, usuario_actual: Usuario, company_id: Optional[UUID], cliente_id: Optional[str]) -> dict:
        ... 