from typing import List
from app.db.repositories.nivel_tecnico import nivel_tecnico_crud
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.nivel_tecnico import NivelTecnico

class NivelTecnicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[NivelTecnico]:
        """Get all available levels"""

        return await nivel_tecnico_crud.get_multi(self.db)