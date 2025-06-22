from app.services.unidad.user_cases.super_admin import SuperAdminUnidadCase
from app.services.unidad.user_cases.admin import AdminUnidadCase
from app.services.unidad.user_cases.supervisor import SupervisorUnidadCase
from app.services.unidad.user_cases.tecnico import TecnicoUnidadCase
from app.services.unidad.user_cases.cliente import ClienteUnidadCase
from app.db.models.usuarios import Rol
from app.services.unidad.interfaces import UnidadCaseInterface

class FabricaDeUnidades:
    @staticmethod
    def get_unidad_case(rol: Rol) -> UnidadCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminUnidadCase()
        elif rol == Rol.ADMIN:
            return AdminUnidadCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorUnidadCase()
        elif rol == Rol.TECHNICIAN:
            return TecnicoUnidadCase()
        elif rol == Rol.CLIENT:
            return ClienteUnidadCase()
        else:
            raise ValueError(f"Rol {rol} no válido para unidades") 