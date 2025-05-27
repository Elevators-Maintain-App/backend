from app.db.models.checklists import Checklist
from app.schemas.checklists import ChecklistCreate, ChecklistUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDChecklist(CRUDBaseRepository[Checklist, ChecklistCreate, ChecklistUpdate]):
    pass

checklist_crud = CRUDChecklist(Checklist)