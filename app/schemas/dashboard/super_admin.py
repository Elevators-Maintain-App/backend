from dataclasses import dataclass

@dataclass
class SuperAdminDashboard:
    usuarios: int
    proyectos: int
    planes: int
    companias: int