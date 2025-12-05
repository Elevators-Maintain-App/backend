# app/api/routes/clientes.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteOut
from app.schemas.proyectos import ProyectoInDBBase
from app.schemas.unidades import UnidadInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.services.cliente.cliente_servicio import ClienteService
from app.auth.firebase import require_role, FirebaseUser
from app.schemas.comunes import PaginacionResponse

router = APIRouter()

# Rutas CRUD normales
@router.get("/", response_model=PaginacionResponse[ClienteOut])
async def get_clientes(
    db: AsyncSession = Depends(get_db),
    usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor")),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros a retornar"),
    search: Optional[str] = Query(None, description="Buscar por nombre o documento"),
    company_id: Optional[str] = Query(None, description="ID de la compañía"),
    tipo_documento_id: Optional[int] = Query(None, description="ID del tipo de documento")
):
    service = ClienteService(db)
    return await service.get_clientes_con_paginacion(usuario_actual=usuario_actual, skip=skip, limit=limit, search=search, company_id=company_id, tipo_documento_id=tipo_documento_id)

@router.get("/{cliente_id}", response_model=ClienteOut)
async def get_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db), usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor", "technician"))):
    service = ClienteService(db)
    return await service.get_by_id(cliente_id, usuario_actual=usuario_actual)

@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    documento: str = Form(...),
    tipo_documento_id: int = Form(...),
    compania_id: UUID = Form(...),
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    pais_id: int = Form(...),
    ciudad: str = Form(...),
    direccion: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor"))
):
    """
    Crea un nuevo cliente. El logo es opcional y se puede subir como archivo.
    """
    service = ClienteService(db)
    
    cliente_data = {
        "documento": documento,
        "tipo_documento_id": tipo_documento_id,
        "compania_id": compania_id,
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "pais_id": pais_id,
        "ciudad": ciudad,
        "direccion": direccion
    }
    
    return await service.create_cliente(cliente_data, logo, usuario_actual=usuario_actual)

@router.put("/{cliente_id}", response_model=ClienteOut)
async def update_cliente(
    cliente_id: UUID,
    cliente_in: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor"))
):
    service = ClienteService(db)
    return await service.update_cliente(cliente_id, cliente_in, usuario_actual=usuario_actual)

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(cliente_id: UUID, db: AsyncSession = Depends(get_db), usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor"))):
    service = ClienteService(db)
    await service.delete_cliente(cliente_id, usuario_actual=usuario_actual)

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
