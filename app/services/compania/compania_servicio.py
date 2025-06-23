from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.db.repositories.compania import CompaniaRepository, compania_crud
from app.db.models.compania import Compania
from app.schemas.compania import CompaniaCreate, CompaniaUpdate, CompaniaOut
from app.db.models.usuarios import Usuario, Rol
from app.auth.firebase import FirebaseUser
from app.services.compania.compania_mapper import compania_to_compania_out
from app.services.compania.user_cases import FabricaDeCompanias
from app.schemas.comunes import PaginacionResponse

class CompaniaService:
    def __init__(self, db: AsyncSession):
        self.repository = CompaniaRepository(db)
        self.db = db
    
    async def get_compania(self, compania_id: str, usuario_actual: Usuario) -> CompaniaOut:
        """
        Obtiene una compañía por su ID basado en los permisos del usuario
        """
        fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
        
        if not fabrica_de_companias.puede_ver_compania(usuario_actual, compania_id):
            raise ForbiddenException("No tienes permisos para consultar esta compañía")
        
        compania = await self.repository.get_with_relations(compania_id)

        if not compania:
            raise NotFoundException(f"Compañía con ID {compania_id} no encontrada")
        
        return compania_to_compania_out(compania)
    
    async def get_companias_con_paginacion(self, usuario_actual: Usuario, skip: Optional[int] = 0, limit: Optional[int] = None, search: Optional[str] = None, tipo_documento_id: Optional[int] = None) -> PaginacionResponse[CompaniaOut]:
        """
        Obtiene compañías con filtros basados en el rol del usuario
        """
        try:
            fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
            filtros = fabrica_de_companias.obtener_filtros_para_listar_companias(usuario_actual, search, tipo_documento_id)

            companias = await compania_crud.get_multi_with_advanced_filters_and_relations(
                self.db, 
                skip=skip, 
                limit=limit, 
                exact_filters=filtros.get("exact_filters", None), 
                ilike_filters=filtros.get("ilike_filters", None), 
                like_filters=filtros.get("like_filters", None)
            )
            total_companias = await self._total_companias_con_filtro(filtros)

            # Map to CompaniaOut using the existing mapper
            return PaginacionResponse(
                data=[compania_to_compania_out(compania) for compania in companias],
                total=total_companias,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            print("**** get_companias", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las compañías")
        
    async def _total_companias_con_filtro(self, filtros: dict) -> int:
        cantidad_de_companias = await compania_crud.get_total_with_advanced_filters(
            self.db, 
            exact_filters=filtros.get("exact_filters", None), 
            ilike_filters=filtros.get("ilike_filters", None), 
            like_filters=filtros.get("like_filters", None)
        )
        return cantidad_de_companias
    async def get_total_companias(self, usuario_actual: Usuario, tipo_documento_id: Optional[int] = None) -> int:
        """
        Obtiene el total de compañías basado en los permisos del usuario
        """
        try:
            fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
            filtro_para_totalizar_companias = fabrica_de_companias.obtener_filtro_para_totalizar_companias(usuario_actual, tipo_documento_id)
            
            cantidad_de_companias = await compania_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar_companias.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar_companias.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar_companias.get("like_filters", None)
            )
            return cantidad_de_companias
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de compañías")

    async def get_companias_basic(self, usuario_actual: Usuario, skip: int = 0, limit: int = 100) -> List[Compania]:
        """
        Método básico para obtener compañías (para compatibilidad con versiones anteriores)
        Solo SuperAdmin tiene acceso a este método
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
    
    async def create_compania(self, compania_in: CompaniaCreate, usuario_actual: FirebaseUser) -> Compania:
        """
        Crea una nueva compañía (solo SuperAdmin)
        """
        fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
        
        if not fabrica_de_companias.puede_gestionar_companias(usuario_actual):
            raise ForbiddenException("No tienes permisos para crear compañías")
        
        # Verificar si ya existe una compañía con ese documento
        existing_compania = await self.repository.get_by_documento(compania_in.documento)
        if existing_compania:
            raise ConflictException(f"Ya existe una compañía con el documento {compania_in.documento}")
        
        # Crear la compañía
        compania = await self.repository.create(obj_in=compania_in)
        return compania
    
    async def update_compania(self, compania_id: str, compania_in: CompaniaUpdate, usuario_actual: Usuario) -> Compania:
        """
        Actualiza una compañía existente
        """
        fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
        
        if not fabrica_de_companias.puede_gestionar_companias(usuario_actual):
            raise ForbiddenException("No tienes permisos para actualizar compañías")
        
        compania = await self.repository.get_with_relations(compania_id)
        if not compania:
            raise NotFoundException(f"Compañía con ID {compania_id} no encontrada")
        
        # Verificar si se está tratando de cambiar el documento a uno que ya existe
        if compania_in.documento and compania_in.documento != compania.documento:
            existing_compania = await self.repository.get_by_documento(compania_in.documento)
            if existing_compania:
                raise ConflictException(f"Ya existe una compañía con el documento {compania_in.documento}")
        
        # Actualizar la compañía
        update_data = compania_in.model_dump(exclude_unset=True)
        updated_compania = await self.repository.update(db_obj=compania, obj_in=update_data)
        return updated_compania
    
    async def delete_compania(self, compania_id: str, usuario_actual: Usuario) -> Compania:
        """
        Elimina una compañía (solo SuperAdmin)
        """
        fabrica_de_companias = FabricaDeCompanias.get_compania_case(usuario_actual.rol)
        
        if not fabrica_de_companias.puede_gestionar_companias(usuario_actual):
            raise ForbiddenException("No tienes permisos para eliminar compañías")
            
        # Solo SuperAdmin puede eliminar compañías
        if usuario_actual.rol != Rol.SUPER_ADMIN:
            raise ForbiddenException("Solo SuperAdmin puede eliminar compañías")
            
        if not fabrica_de_companias.puede_ver_compania(usuario_actual, compania_id):
            raise ForbiddenException("No tienes permisos para acceder a esta compañía")
        
        compania = await self.repository.get_with_relations(compania_id)
        if not compania:
            raise NotFoundException(f"Compañía con ID {compania_id} no encontrada")
            
        deleted_compania = await self.repository.delete(id=compania_id)
        return deleted_compania 