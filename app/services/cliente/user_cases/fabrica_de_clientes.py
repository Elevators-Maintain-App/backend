from app.services.cliente.user_cases.super_admin import SuperAdminClienteCase
from app.services.cliente.user_cases.admin import AdminClienteCase
from app.services.cliente.user_cases.supervisor import SupervisorClienteCase
from app.services.cliente.user_cases.tecnico import TecnicoClienteCase
from app.services.cliente.user_cases.cliente import ClienteClienteCase
from app.db.models.usuarios import Rol
from app.services.cliente.interfaces import ClienteCaseInterface

class FabricaDeClientes:
    @staticmethod
    def get_cliente_case(rol: Rol) -> ClienteCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminClienteCase()
        elif rol == Rol.ADMIN:
            return AdminClienteCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorClienteCase()
        elif rol == Rol.TECHNICIAN:
            return TecnicoClienteCase()
        elif rol == Rol.CLIENT:
            return ClienteClienteCase()
        else:
            raise ValueError(f"Rol {rol} no válido para clientes") 