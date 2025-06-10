from app.db.repositories.pais import PaisRepository
from sqlalchemy.ext.asyncio import AsyncSession

class PaisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaisRepository()

    async def get_paises(self):
        return await self.repository.get_multi(self.db)