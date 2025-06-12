from dataclasses import dataclass

@dataclass
class SupervisorDashboard:
    usuarios: int
    proyectos: int
    planes: int
    companias: int