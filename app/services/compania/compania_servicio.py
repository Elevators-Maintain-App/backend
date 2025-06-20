from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.db.repositories.compania import CompaniaRepository
from app.db.models.compania import Compania
from app.schemas.compania import CompaniaCreate, CompaniaUpdate
from app.db.models.usuarios import Usuario, Rol
from app.auth.firebase import FirebaseUser
from app.services.compania.compania_mapper import compania_to_compania_out


class CompaniaService:
    def __init__(self, db: AsyncSession):
        self.repository = CompaniaRepository(db)
    
    async def get_compania(self, compania_id: str, usuario_actual: FirebaseUser) -> Compania:
        """
        Obtiene una compañía por su ID
        """
        if usuario_actual.rol != Rol.SUPER_ADMIN:
            raise ForbiddenException("No tienes permisos para consultar esta compañía")
        
        compania = await self.repository.get_with_relations(compania_id)

        if not compania:
            raise NotFoundException(f"Compañía con ID {compania_id} no encontrada")
        
        return compania_to_compania_out(compania)
    
    async def get_companias(self, usuario_actual: Usuario, skip: int = 0, limit: int = 100) -> List[Compania]:
        """
        Obtiene todas las compañías con paginación
        """
        if usuario_actual.rol != Rol.SUPER_ADMIN:
            raise ForbiddenException("No tienes permisos para obtener todas las compañías")
        
        return await self.repository.list(skip=skip, limit=limit)
    
    async def get_compania_by_documento(self, documento: str) -> Optional[Compania]:
        """
        Obtiene una compañía por su documento
        """
        return await self.repository.get_by_documento(documento)
    
    async def get_companias_by_tipo_documento(
        self, tipo_documento_id: int, skip: int = 0, limit: int = 100
    ) -> List[Compania]:
        """
        Obtiene todas las compañías por tipo de documento
        """
        return await self.repository.get_by_tipo_documento(
            tipo_documento_id=tipo_documento_id, skip=skip, limit=limit
        )
    
    async def create_compania(self, compania_in: CompaniaCreate) -> Compania:
        """
        Crea una nueva compañía
        """
        # Verificar si ya existe una compañía con ese documento
        existing_compania = await self.repository.get_by_documento(compania_in.documento)
        if existing_compania:
            raise ConflictException(f"Ya existe una compañía con el documento {compania_in.documento}")
        
        # Crear la compañía
        compania = await self.repository.create(obj_in=compania_in)
        return compania
    
    async def update_compania(self, compania_id: str, compania_in: CompaniaUpdate) -> Compania:
        """
        Actualiza una compañía existente
        """
        compania = await self.get_compania(compania_id)
        
        # Verificar si se está tratando de cambiar el documento a uno que ya existe
        if compania_in.documento and compania_in.documento != compania.documento:
            existing_compania = await self.repository.get_by_documento(compania_in.documento)
            if existing_compania:
                raise ConflictException(f"Ya existe una compañía con el documento {compania_in.documento}")
        
        # Actualizar la compañía
        update_data = compania_in.model_dump(exclude_unset=True)
        updated_compania = await self.repository.update(db_obj=compania, obj_in=update_data)
        return updated_compania
    
    async def delete_compania(self, compania_id: str) -> Compania:
        """
        Elimina una compañía
        """
        compania = await self.get_compania(compania_id)
        deleted_compania = await self.repository.delete(id=compania_id)
        return deleted_compania 