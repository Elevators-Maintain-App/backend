# app/api/routes/usuarios.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut, UserOut, CountOut
from app.services.usuarios import UsuarioService
from app.auth.firebase import require_role, db_firestore
from app.auth.firebase import get_current_firebase_user
from uuid import UUID
from app.db.models.compania import Compania as CompaniaModel

router = APIRouter()

# Rutas para SuperAdmin
@router.get(
    "/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK
)
async def count_all_users(
    user=Depends(require_role("superAdmin"))
):
    """
    (superAdmin) Retorna la cantidad total de usuarios en Firebase.
    """
    total = 0
    for _ in db_firestore.collection("users").stream():
        total += 1
    return {"count": total}

@router.get(
    "/all",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK
)
async def list_all_users(
    user=Depends(require_role("superAdmin"))
):
    """
    (superAdmin) Lista todos los usuarios registrados en Firebase.
    """
    salida: List[UserOut] = []
    for doc in db_firestore.collection("users").stream():
        data = doc.to_dict()
        salida.append(UserOut(
            uid=doc.id,
            email=data.get("email"),
            display_name=data.get("display_name"),
            company_id=data.get("company_id"),
            role=data.get("rol"),
            photo_url=data.get("photo_url"),
        ))
    return salida

# Ruta para detalle de usuario Admin y SuperAdmin
@router.get(
    "/all/{uid}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK
)
async def get_user_detail(
    uid: str = Path(..., description="UID del usuario en Firebase"),
    current_user=Depends(require_role("superAdmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    (superAdmin) Devuelve todos los datos de un usuario en Firebase dado su UID,
    pero reemplaza company_id por el nombre de la compañía.
    """
    doc = db_firestore.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {uid} no encontrado en Firebase"
        )
    data = doc.to_dict()

    if current_user.role == "admin" and data.get("company_id") != current_user.company_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Permisos insuficientes para ver este usuario"
        )

    company_uid = data.get("company_id")
    company_name = None
    try:
        company_uuid = UUID(company_uid)
        compania = await db.get(CompaniaModel, company_uuid)
        company_name = compania.nombre if compania else None
    except Exception:
        company_name = None

    return UserOut(
        uid=doc.id,
        email=data.get("email"),
        display_name=data.get("display_name"),
        company_id=company_name,
        role=data.get("rol"),
        photo_url=data.get("photo_url"),
    )

# Rutas para admin

@router.get(
    "/company/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK
)
async def count_company_users(
    user=Depends(require_role("admin"))
):
    """
    (admin) Cantidad de usuarios en la misma compañía.
    """
    total = 0
    for _ in db_firestore.collection("users")\
            .where("company_id", "==", user.company_id)\
            .stream():
        total += 1
    return {"count": total}

@router.get(
    "/company/all",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK
)
async def list_company_users(
    user=Depends(require_role("admin"))
):
    """
    (admin) Lista todos los usuarios de la misma compañía.
    """
    salida: List[UserOut] = []
    for doc in db_firestore.collection("users")\
            .where("company_id", "==", user.company_id)\
            .stream():
        data = doc.to_dict()
        salida.append(UserOut(
            uid=doc.id,
            email=data.get("email"),
            display_name=data.get("display_name"),
            company_id=data.get("company_id"),
            role=data.get("rol"),
            photo_url=data.get("photo_url"),
        ))
    return salida


@router.get("/", response_model=List[UsuarioOut])
async def listar_usuarios(db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.get_all()

@router.get("/{uid}", response_model=UsuarioOut)
async def obtener_usuario(uid: str = Path(...), db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.get_by_uid(uid)

@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def crear_usuario(usuario_in: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.create(usuario_in)

@router.put("/{uid}", response_model=UsuarioOut)
async def actualizar_usuario(uid: str, usuario_in: UsuarioUpdate, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.update(uid, usuario_in)

@router.delete("/{uid}", response_model=UsuarioOut)
async def eliminar_usuario(uid: str, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.delete(uid)
