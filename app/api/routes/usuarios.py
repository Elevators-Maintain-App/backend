# app/api/routes/usuarios.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.services.usuarios import UsuarioService
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[UsuarioOut])
async def listar_usuarios(db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.get_all()

@router.get("/protegido", response_model=dict)
async def solo_para_supervisores(current_user = Depends(require_role("supervisor"))):
    return {"mensaje": f"Hola {current_user.full_name}, eres supervisor autorizado"}

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


