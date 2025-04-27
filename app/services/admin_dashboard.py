# app/services/admin_dashboard.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.tecnicos import Tecnico
from app.db.models.supervisores import Supervisor
from app.db.models.clientes import Cliente

class AdminDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usuarios(self):
        """
        Devuelve una lista de todos los usuarios del sistema.
        """
        tecnicos_result = await self.db.execute(select(Tecnico))
        supervisores_result = await self.db.execute(select(Supervisor))
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
        tecnicos_count = await self.db.execute(select(func.count(Tecnico.id)))
        supervisores_count = await self.db.execute(select(func.count(Supervisor.id)))
        clientes_count = await self.db.execute(select(func.count(Cliente.id)))

        return {
            "tecnicos": tecnicos_count.scalar_one(),
            "supervisores": supervisores_count.scalar_one(),
            "clientes": clientes_count.scalar_one()
        }
