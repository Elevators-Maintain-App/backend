from dataclasses import dataclass

@dataclass
class ClienteDashboard:
    usuarios: int
    proyectos: int
    planes: int
    companias: int