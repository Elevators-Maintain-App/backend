from dataclasses import dataclass

@dataclass
class TechnicianDashboard:
    ordenes_trabajo: int
    validadas: int
    pendientes: int