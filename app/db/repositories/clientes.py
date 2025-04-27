from app.db.models.clientes import Cliente
from app.schemas.clientes import ClienteCreate, ClienteUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDClientes(CRUDBaseRepository[Cliente, ClienteCreate, ClienteUpdate]):
    pass

cliente_crud = CRUDClientes(Cliente)