from app.services.compania.user_cases.super_admin import SuperAdminCompaniaCase
from app.services.compania.user_cases.admin import AdminCompaniaCase
from app.services.compania.user_cases.supervisor import SupervisorCompaniaCase
from app.db.models.usuarios import Rol
from app.services.compania.interfaces import CompaniaCaseInterface

class FabricaDeCompanias:
    @staticmethod
    def get_compania_case(rol: Rol) -> CompaniaCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminCompaniaCase()
        elif rol == Rol.ADMIN:
            return AdminCompaniaCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorCompaniaCase()
        else:
            raise ValueError(f"Rol {rol} no válido para compañías") 