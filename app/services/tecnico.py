from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.usuario.usuarios import UsuarioService
from app.schemas.comunes import PaginacionResponse
from app.db.models.usuarios import Usuario  
from app.db.models.usuarios import Rol

ROL_TECNICO = Rol.TECHNICIAN.name

class TecnicoService:
    """Filtra los usuarios con rol 'technician' respetando
    las reglas de visibilidad ya implementadas en UsuarioService."""
    def __init__(self, db: AsyncSession) -> None:
        self._usuario_service = UsuarioService(db)

    async def get_tecnicos_con_paginacion(
        self,
        *,
        usuario_actual: Usuario,
        limit: int = 1000,
        skip: int = 0,
        search: Optional[str] = None,
    ) -> PaginacionResponse:
        return await self._usuario_service.get_usuarios_con_paginacion(
            usuario_actual=usuario_actual,
            skip=skip,
            limit=limit,
            search=search,
            rol=ROL_TECNICO,          
        )