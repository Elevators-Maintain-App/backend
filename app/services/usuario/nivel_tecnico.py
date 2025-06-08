from typing import List
from app.db.repositories.nivel_tecnico import nivel_tecnico_crud
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.nivel_tecnico import NivelTecnico
from app.schemas.nivel_tecnico import NivelTecnicoCreate, NivelTecnicoUpdate
from uuid import UUID

class NivelTecnicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_niveles_tecnicos(self) -> List[NivelTecnico]:
        """Get all available levels"""

        return await nivel_tecnico_crud.get_multi(self.db)
    
    async def create_nivel_tecnico(self, nivel_tecnico: NivelTecnicoCreate) -> NivelTecnico:
        """Create a new level"""
        return await nivel_tecnico_crud.create(self.db, nivel_tecnico)
    
    async def update_nivel_tecnico(self, nivel_tecnico_id: UUID, nivel_tecnico: NivelTecnicoUpdate) -> NivelTecnico:
        """Update a level"""
        return await nivel_tecnico_crud.update(self.db, nivel_tecnico_id, nivel_tecnico)
    
    async def delete_nivel_tecnico(self, nivel_tecnico_id: UUID) -> NivelTecnico:
        """Delete a level"""
        return await nivel_tecnico_crud.delete(self.db, nivel_tecnico_id)