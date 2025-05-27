from app.db.models.hojas_de_vida import HojaDeVida
from app.schemas.hojas_de_vida import HojaDeVidaCreate, HojaDeVidaUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDHojasDeVida(CRUDBaseRepository[HojaDeVida, HojaDeVidaCreate, HojaDeVidaUpdate]):
    pass

hoja_de_vida_crud = CRUDHojasDeVida(HojaDeVida)