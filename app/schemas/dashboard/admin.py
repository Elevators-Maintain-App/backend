from dataclasses import dataclass

@dataclass
class AdminDashboard:
    clientes: int
    proyectos: int
    usuarios: int
    ordenes_trabajo: int
    unidades: int