from app.services.usuario.user_cases.super_admin import SuperAdminCase
from app.services.usuario.user_cases.admin import AdminCase
from app.services.usuario.user_cases.supervisor import SupervisorCase
from app.db.models.usuarios import Rol
from app.services.usuario.interfaces import UsuarioCaseInterface

class FabricaDeUsuarios:
    @staticmethod
    def get_user_case(rol: Rol) -> UsuarioCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminCase()
        elif rol == Rol.ADMIN:
            return AdminCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorCase()
        else:
            raise ValueError(f"Rol {rol} no válido")