from dataclasses import dataclass
from typing import List

@dataclass
class ClienteDashboardProyecto:
    nombre_proyecto: str
    estado: str
    cantidad_unidades: int
    cantidad_ordenes_activas: int
    tiene_mantenimientos_por_vencer: bool
    fecha_de_vencimiento: str
    

@dataclass
class ClienteDashboard:
    proyectos: List[ClienteDashboardProyecto]