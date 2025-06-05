# app/api/routes/compania.py

from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from typing import List, Dict, Optional
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,  func

from app.db.session import get_db
from app.services.compania import CompaniaService
from app.schemas.compania import CompaniaCreate, CompaniaUpdate, Compania
from app.auth.firebase import require_role, get_firestore_client
from app.schemas.usuarios import UserOut, UsuarioResponse
from app.db.models.compania import Compania as CompaniaModel
from app.db.repositories import compania_crud

router = APIRouter()

@router.get(
    "/",
    response_model=List[Compania]
)
async def get_companias(
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros a retornar"),
):
    """
    (superAdmin) Obtiene todas las compañías con paginación
    """
    service = CompaniaService(db)
    return await service.get_companias(skip=skip, limit=limit)

@router.get(
    "/count",
    response_model=Compania,
    status_code=status.HTTP_200_OK
)
async def count_companias(
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db)
):
    """
    (superAdmin) Retorna la cantidad de compañías registradas.
    """
    result = await db.execute(select(func.count()).select_from(CompaniaModel))
    total = result.scalar_one()
    return {"count": total}

@router.get(
    "/users/count",
    response_model=Dict[str, int],
    status_code=status.HTTP_200_OK
)
async def count_users_per_company(
    user=Depends(require_role("superAdmin")),
):
    """
    (superAdmin) Devuelve el número de usuarios por cada compañía registrada.
    {
      "<compania_id>": 12,
      "<otra_compania_id>": 5,
      ...
    }
    """
    # Listamos todas las compañías activas
    # (podemos paginar o filtrar, aquí asumimos pocas compañías)
    # En este caso saltamos el repositorio SQL y leemos directamente Firestore:
    counts: Dict[str,int] = {}
    # Alternativa: puedes recoger todos los IDs desde Firestore mismo:
    users = get_firestore_client().collection("users").stream()
    for doc in users:
        cid = doc.to_dict().get("company_id")
        if not cid:
            continue
        counts[cid] = counts.get(cid, 0) + 1
    return counts

@router.post(
    "/",
    response_model=Compania,
    status_code=status.HTTP_201_CREATED
)
async def create_compania(
    compania_in: CompaniaCreate,
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Crea una nueva compañía
    """
    service = CompaniaService(db)
    return await service.create_compania(compania_in=compania_in)

@router.get(
    "/{compania_id}",
    response_model=Compania
)
async def get_compania(
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Obtiene una compañía por su ID
    """
    service = CompaniaService(db)
    compania = await service.get_compania(compania_id=compania_id)
    return compania

@router.put(
    "/{compania_id}",
    response_model=Compania
)
async def update_compania(
    compania_in: CompaniaUpdate,
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Actualiza una compañía existente
    """
    service = CompaniaService(db)
    return await service.update_compania(
        compania_id=compania_id, 
        compania_in=compania_in
    )

@router.delete(
    "/{compania_id}",
    response_model=Compania
)
async def delete_compania(
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Elimina una compañía
    """
    service = CompaniaService(db)
    return await service.delete_compania(compania_id=compania_id)

@router.get(
    "/documento/{documento}",
    response_model=Compania
)
async def read_compania_by_documento(
    documento: str = Path(..., description="Documento de la compañía"),
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Obtiene una compañía por su documento
    """
    service = CompaniaService(db)
    compania = await service.get_compania_by_documento(documento=documento)
    if not compania:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compañía con documento {documento} no encontrada"
        )
    return compania

@router.get(
    "/tipo-documento/{tipo_documento_id}",
    response_model=List[Compania]
)
async def read_companias_by_tipo_documento(
    tipo_documento_id: int = Path(..., description="ID del tipo de documento"),
    user=Depends(require_role("superAdmin")),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros a retornar"),
    db: AsyncSession = Depends(get_db),
):
    """
    (superAdmin) Obtiene todas las compañías por tipo de documento
    """
    service = CompaniaService(db)
    return await service.get_companias_by_tipo_documento(
        tipo_documento_id=tipo_documento_id, 
        skip=skip, 
        limit=limit
    )

@router.get("/{compania_id}/users", response_model=List[UsuarioResponse], dependencies=[Depends(require_role("superAdmin"))])
async def get_users_by_company(
    compania_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener usuarios de una compañía específica desde Firebase.
    Solo superAdmin puede acceder.
    """
    # Verificar que la compañía existe
    compania = await compania_crud.get_by_id(db, compania_id)
    if not compania:
        raise HTTPException(status_code=404, detail="Compañía no encontrada")
    
    try:
        # Obtener usuarios de Firebase filtrados por company_id
        users = get_firestore_client().collection("users").stream()
        usuarios_response = []
        count = 0
        skipped = 0
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            
            # Filtrar por company_id
            if user_data.get("company_id") == str(compania_id):
                # Aplicar skip
                if skipped < skip:
                    skipped += 1
                    continue
                
                # Aplicar limit
                if count >= limit:
                    break
                
                usuarios_response.append(UsuarioResponse(
                    uid=user_doc.id,
                    email=user_data.get("email", ""),
                    display_name=user_data.get("display_name", ""),
                    document_id=user_data.get("document_id", ""),
                    document_type=user_data.get("document_type", ""),
                    document_type_name=user_data.get("document_type_name", ""),
                    company_id=user_data.get("company_id", ""),
                    company_name=user_data.get("company_name", ""),
                    photo_url=user_data.get("photo_url"),
                    rol=user_data.get("rol", ""),
                    is_active=user_data.get("is_active", True),
                    created_at=user_data.get("created_at"),
                    updated_at=user_data.get("updated_at")
                ))
                count += 1
        
        return usuarios_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(e)}"
        )

@router.delete("/{compania_id}/users", response_model=dict, dependencies=[Depends(require_role("superAdmin"))])
async def delete_users_by_company(
    compania_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar todos los usuarios de una compañía específica desde Firebase.
    Solo superAdmin puede acceder.
    """
    # Verificar que la compañía existe
    compania = await compania_crud.get_by_id(db, compania_id)
    if not compania:
        raise HTTPException(status_code=404, detail="Compañía no encontrada")
    
    try:
        # Obtener usuarios de Firebase filtrados por company_id
        users_ref = get_firestore_client().collection("users").where("company_id", "==", str(compania_id))
        users_query = users_ref.stream()
        
        deleted_count = 0
        errors = []
        
        for user_doc in users_query:
            try:
                # Eliminar el documento del usuario
                user_doc.reference.delete()
                deleted_count += 1
            except Exception as delete_error:
                errors.append(f"Error al eliminar usuario {user_doc.id}: {str(delete_error)}")
        
        response = {
            "message": f"Eliminación completada para compañía {compania_id}",
            "deleted_users": deleted_count,
            "company_id": compania_id,
            "company_name": compania.nombre
        }
        
        if errors:
            response["errors"] = errors
            
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuarios: {str(e)}"
        )



