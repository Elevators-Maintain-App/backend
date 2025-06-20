# app/api/routes/clientes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteOut
from app.schemas.proyectos import ProyectoInDBBase
from app.schemas.unidades import UnidadInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.services.cliente.cliente_servicio import ClienteService
from app.auth.firebase import require_role, FirebaseUser

router = APIRouter()

# Rutas CRUD normales
@router.get("/", response_model=List[ClienteOut])
async def get_clientes(db: AsyncSession = Depends(get_db), usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor"))):
    service = ClienteService(db)
    return await service.get_all(usuario_actual=usuario_actual)

@router.get("/{cliente_id}", response_model=ClienteOut)
async def get_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db), usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor"))):
    service = ClienteService(db)
    return await service.get_by_id(cliente_id, usuario_actual=usuario_actual)

@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(cliente_in: ClienteCreate, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    return await service.create(cliente_in)

@router.put("/{cliente_id}", response_model=ClienteOut)
async def update_cliente(cliente_id: UUID, cliente_in: ClienteUpdate, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    return await service.update(cliente_id, cliente_in)

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    await service.delete(cliente_id)

# Rutas Especiales 

@router.get("/{cliente_id}/proyectos", response_model=List[ProyectoInDBBase], description="Listar todos los proyectos asociados a un cliente específico.")
async def get_proyectos_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    return await service.get_proyectos(cliente_id)

@router.get("/{cliente_id}/unidades", response_model=List[UnidadInDBBase], description="Listar todas las unidades (ascensores, escaleras) asociadas a un cliente.")
async def get_unidades_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    return await service.get_unidades(cliente_id)

@router.get("/{cliente_id}/ordenes-trabajo", response_model=List[OrdenDeTrabajoInDBBase], description="Listar todas las órdenes de trabajo relacionadas a un cliente.")
async def get_ordenes_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ClienteService(db)
    return await service.get_ordenes_trabajo(cliente_id)
