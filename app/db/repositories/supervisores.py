from app.db.models.supervisores import Supervisor
from app.schemas.supervisores import SupervisorCreate, SupervisorUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDSupervisores(CRUDBaseRepository[Supervisor, SupervisorCreate, SupervisorUpdate]):
    pass

supervisor_crud = CRUDSupervisores(Supervisor)