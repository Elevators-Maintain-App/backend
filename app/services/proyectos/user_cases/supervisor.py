from app.db.models.usuarios import Usuario
from app.services.proyectos.interfaces import ProyectoCaseInterface
from typing import Optional
from uuid import UUID
from app.schemas.proyectos import ProyectoCreate, ProyectoCreateInDB
from app.auth.firebase import FirebaseUser


class SupervisorProyectoCase(ProyectoCaseInterface):
    def obtener_filtros_para_listar_proyectos(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str] = None, cliente_id: Optional[str] = None) -> dict:
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"

        return filters
    
    def obtener_filtro_para_totalizar_proyectos(self, usuario_actual: Usuario, company_id: Optional[str] = None, cliente_id: Optional[str] = None) -> dict:
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        return filters 
    
    def obtener_payload_para_crear_proyecto(self, proyecto_in: ProyectoCreate, user: FirebaseUser) -> ProyectoCreateInDB:
        raise NotImplementedError("No se puede crear un proyecto desde el rol de supervisor")