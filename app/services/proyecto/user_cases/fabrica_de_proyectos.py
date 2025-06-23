from app.services.proyecto.user_cases.super_admin import SuperAdminProyectoCase
from app.services.proyecto.user_cases.admin import AdminProyectoCase
from app.services.proyecto.user_cases.supervisor import SupervisorProyectoCase
from app.db.models.usuarios import Rol
from app.services.proyecto.interfaces import ProyectoCaseInterface

class FabricaDeProyectos:
    @staticmethod
    def get_proyecto_case(rol: Rol) -> ProyectoCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminProyectoCase()
        elif rol == Rol.ADMIN:
            return AdminProyectoCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorProyectoCase()
        else:
            raise ValueError(f"Rol {rol} no válido para proyectos") 