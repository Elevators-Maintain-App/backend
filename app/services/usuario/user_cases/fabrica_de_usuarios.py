from app.services.usuario.user_cases.super_admin import SuperAdminCase
from app.services.usuario.user_cases.admin import AdminCase
from app.db.models.usuarios import Rol
from app.services.usuario.interfaces import UsuarioCaseInterface

class FabricaDeUsuarios:
    @staticmethod
    def get_user_case(rol: Rol) -> UsuarioCaseInterface:
        if rol == Rol.superAdmin:
            return SuperAdminCase()
        elif rol == Rol.admin:
            return AdminCase()
        else:
            raise ValueError(f"Rol {rol} no válido")