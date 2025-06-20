from dataclasses import dataclass

@dataclass
class SupervisorDashboard:
    ordenes_trabajo: int
    validadas: int
    pendientes: int