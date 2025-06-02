# app/api/routes/compania.py

from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from typing import List, Dict
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,  func

from app.db.session import get_db
from app.services.compania import CompaniaService
from app.schemas.compania import CompaniaCreate, CompaniaUpdate, Compania
from app.auth.firebase import require_role, db_firestore
from app.schemas.usuarios import UserOut
from app.db.models.compania import Compania as CompaniaModel

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
    users = db_firestore.collection("users").stream()
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

@router.get(
    "/{compania_id}/users",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK
)
async def list_users_by_company(
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    user=Depends(require_role("superAdmin")),
):
    """
    (superAdmin) Lista todos los usuarios que pertenecen a esta compañía (según Firestore).
    """
    # Consulta en Firestore la colección "users" con company_id igual a este ID
    users_ref = db_firestore.collection("users").where("company_id", "==", str(compania_id))
    docs = users_ref.stream()
    salida = []
    for doc in docs:
        data = doc.to_dict()
        salida.append(UserOut(
            uid=doc.id,
            email=data.get("email"),
            display_name=data.get("display_name"),
            company_id=data.get("company_id"),
            role=data.get("role"),
        ))
    return salida



