from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.usuarios import Usuario
from app.db.models.clientes import Cliente

class AdminDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usuarios(self):
        """
        Devuelve una lista de todos los usuarios del sistema (técnicos y supervisores) y clientes.
        """
        tecnicos_result = await self.db.execute(
            select(Usuario).where(Usuario.role == "tecnico")
        )
        supervisores_result = await self.db.execute(
            select(Usuario).where(Usuario.role == "supervisor")
        )
        clientes_result = await self.db.execute(select(Cliente))

        return {
            "tecnicos": tecnicos_result.scalars().all(),
            "supervisores": supervisores_result.scalars().all(),
            "clientes": clientes_result.scalars().all()
        }

    async def get_estadisticas_usuarios(self):
        """
        Devuelve estadísticas básicas de usuarios: cantidad de técnicos, supervisores y clientes.
        """
        tecnicos_count = await self.db.execute(
            select(func.count()).where(Usuario.role == "tecnico")
        )
        supervisores_count = await self.db.execute(
            select(func.count()).where(Usuario.role == "supervisor")
        )
        clientes_count = await self.db.execute(select(func.count(Cliente.id)))

        return {
            "tecnicos": tecnicos_count.scalar_one(),
            "supervisores": supervisores_count.scalar_one(),
            "clientes": clientes_count.scalar_one()
        }
