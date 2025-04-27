from app.db.models.proyectos import Proyecto
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDProyectos(CRUDBaseRepository[Proyecto, ProyectoCreate, ProyectoUpdate]):
    pass

proyecto_crud = CRUDProyectos(Proyecto)