from app.db.models.usuarios import Usuario
from app.services.proyecto.interfaces import ProyectoCaseInterface
from typing import Optional
from uuid import UUID

class SuperAdminProyectoCase(ProyectoCaseInterface):
    def obtener_filtros_para_listar_proyectos(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], cliente_id: Optional[str]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if company_id:
            filters["exact_filters"]["company_id"] = UUID(company_id)
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters
    
    def obtener_filtro_para_totalizar_proyectos(self, usuario_actual: Usuario, company_id: Optional[UUID], cliente_id: Optional[str]) -> dict:
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }

        if company_id:
            filters["exact_filters"]["company_id"] = company_id
        if cliente_id:
            filters["exact_filters"]["cliente_id"] = cliente_id

        return filters 