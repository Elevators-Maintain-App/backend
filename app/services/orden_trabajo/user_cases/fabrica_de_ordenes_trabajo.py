from app.services.orden_trabajo.user_cases.super_admin import SuperAdminOrdenTrabajoCase
from app.services.orden_trabajo.user_cases.admin import AdminOrdenTrabajoCase
from app.services.orden_trabajo.user_cases.supervisor import SupervisorOrdenTrabajoCase
from app.services.orden_trabajo.user_cases.tecnico import TecnicoOrdenTrabajoCase
from app.services.orden_trabajo.user_cases.cliente import ClienteOrdenTrabajoCase
from app.db.models.usuarios import Rol
from app.services.orden_trabajo.interfaces import OrdenTrabajoCaseInterface

class FabricaDeOrdenesTabajo:
    @staticmethod
    def get_orden_trabajo_case(rol: Rol) -> OrdenTrabajoCaseInterface:
        if rol == Rol.SUPER_ADMIN:
            return SuperAdminOrdenTrabajoCase()
        elif rol == Rol.ADMIN:
            return AdminOrdenTrabajoCase()
        elif rol == Rol.SUPERVISOR:
            return SupervisorOrdenTrabajoCase()
        elif rol == Rol.TECHNICIAN:
            return TecnicoOrdenTrabajoCase()
        elif rol == Rol.CLIENT:
            return ClienteOrdenTrabajoCase()
        else:
            raise ValueError(f"Rol {rol} no válido para órdenes de trabajo") 