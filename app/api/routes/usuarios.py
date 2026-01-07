# app/api/routes/usuarios.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.db.session import get_db
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut, UserOut, CountOut
from app.schemas.comunes import PaginacionResponse
from app.services.usuario.usuarios import UsuarioService
from app.auth.firebase import require_role, get_firestore_client
from app.auth.firebase import get_current_firebase_user
from uuid import UUID
from app.db.models.compania import Compania as CompaniaModel
from app.services.notificaciones.notificacion_service import NotificacionService
from app.services.notificaciones.models.notificacion_model import NotificacionModel, DestinatarioModel, TipoNotificacion
from app.services.notificaciones.templates import TemplateManager
from app.core.config import settings
from app.db.models.usuarios import Rol

router = APIRouter()

@router.get("/{uid}", response_model=UsuarioOut)
async def obtener_usuario(uid: str = Path(...), db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.get_by_uid(uid)

@router.get("/", response_model=PaginacionResponse[UsuarioOut], dependencies=[Depends(require_role("superAdmin", "admin", "supervisor"))])
async def get_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    rol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor"))
):
    """
    Obtener lista de usuarios desde Firebase con filtros opcionales.
    """
    try:
        service = UsuarioService(db)
        usuarios = await service.get_usuarios_con_paginacion(usuario_actual, skip, limit, search, company_id, rol)
        return usuarios
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(e)}"
        )

@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    company_id: Optional[UUID] = Form(None),
    display_name: str = Form(...),
    document_id: str = Form(...),
    document_type_id: int = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    rol: str = Form(...),
    client_id: Optional[UUID] = Form(None),
    nivel: Optional[str] = Form(None),
    zona_geografica_id: Optional[UUID] = Form(None),
    is_active: Optional[bool] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
):
    try:
        rol_enum = Rol(rol)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido: {rol}. Roles válidos: {[r.value for r in Rol]}"
        )
    
    usuario_data = {
        "company_id": company_id,
        "display_name": display_name,
        "document_id": document_id,
        "document_type_id": document_type_id,
        "email": email,
        "phone_number": phone_number,
        "rol": rol_enum,
        "client_id": client_id,
        "nivel": nivel,
        "zona_geografica_id": zona_geografica_id,
        "is_active": is_active
    }
    
    service = UsuarioService(db)
    return await service.create(usuario_actual, usuario_data, photo)

@router.put("/{uid}", response_model=UsuarioOut)
async def actualizar_usuario(uid: str, usuario_in: UsuarioUpdate, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.update(uid, usuario_in)

@router.delete("/{uid}", response_model=UsuarioOut, dependencies=[Depends(require_role("superAdmin", "admin", "supervisor"))])
async def eliminar_usuario(uid: str, db: AsyncSession = Depends(get_db)):
    service = UsuarioService(db)
    return await service.delete(uid)

# """

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
    for _ in get_firestore_client().collection("users").stream():
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
    for doc in get_firestore_client().collection("users").stream():
        data = doc.to_dict()
        salida.append(UserOut(
            uid=doc.id,
            email=data.get("email"),
            display_name=data.get("display_name"),
            company_id=data.get("company_id"),
            role=data.get("rol"),
            photo_url=data.get("photo_url"),
            company_name=data.get("company_name"),
        ))
    return salida

# superAdmin: contar todos los clientes
@router.get(
    "/clients/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK,
    summary="(superAdmin) Cantidad total de clientes"
)
async def count_all_clients(
    user=Depends(require_role("superAdmin")),
):
    total = 0
    for _ in get_firestore_client().collection("users") \
            .where("rol", "==", "client") \
            .stream():
        total += 1
    return {"count": total}

# superAdmin: listar todos los clientes
@router.get(
    "/clients/all",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
    summary="(superAdmin) Lista todos los clientes"
)
async def list_all_clients(
    user=Depends(require_role("superAdmin")),
):
    salida: List[UserOut] = []
    for doc in get_firestore_client().collection("users") \
            .where("rol", "==", "client") \
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
    for _ in get_firestore_client().collection("users")\
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
    user=Depends(require_role("admin", "supervisor"))
):
    """
    (admin) Lista todos los usuarios de la misma compañía.
    """
    salida: List[UserOut] = []
    for doc in get_firestore_client().collection("users")\
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

# admin: contar clientes de su compañía
@router.get(
    "/clients/company/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK,
    summary="(admin) Cantidad de clientes en su compañía"
)
async def count_company_clients(
    user=Depends(require_role("admin")),
):
    total = 0
    for _ in get_firestore_client().collection("users") \
            .where("rol", "==", "client") \
            .where("company_id", "==", user.company_id) \
            .stream():
        total += 1
    return {"count": total}

# admin: listar clientes de su compañía
@router.get(
    "/clients/company/all",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
    summary="(admin) Lista clientes de su compañía"
)
async def list_company_clients(
    user=Depends(require_role("admin")),
):
    salida: List[UserOut] = []
    for doc in get_firestore_client().collection("users") \
            .where("rol", "==", "client") \
            .where("company_id", "==", user.company_id) \
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
    doc = get_firestore_client().collection("users").document(uid).get()
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

@router.get("/by-role/{rol}", response_model=PaginacionResponse[UsuarioOut], dependencies=[Depends(require_role("superAdmin", "operativo"))])
async def get_usuarios_by_role(
    rol: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener usuarios por rol desde Firebase.
    superAdmin y operativo pueden acceder.
    """
    try:
        # Count total users with filters
        total = 0
        for _ in get_firestore_client().collection("users") \
                .where("rol", "==", rol).stream():
            user_data = _.to_dict()
            
            if company_id and user_data.get("company_id") != company_id:
                continue
            
            total += 1
        
        # Get paginated users with filters
        usuarios = []
        count = 0
        skipped = 0
        
        for doc in get_firestore_client().collection("users") \
                .where("rol", "==", rol).stream():
            user_data = doc.to_dict()
            
            if company_id and user_data.get("company_id") != company_id:
                continue
            
            # Apply skip
            if skipped < skip:
                skipped += 1
                continue
            
            # Apply limit
            if count >= limit:
                break
            
            usuarios.append(UsuarioOut(
                uid=doc.id,
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
        
        return PaginacionResponse(
            data=usuarios,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios por rol: {str(e)}"
        )

@router.get("/by-company/{company_id}", response_model=PaginacionResponse[UsuarioOut], dependencies=[Depends(require_role("superAdmin", "operativo", "cliente"))])
async def get_usuarios_by_company(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    rol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener usuarios por compañía desde Firebase.
    superAdmin, operativo y cliente pueden acceder.
    """
    try:
        # Count total users with filters
        total = 0
        for _ in get_firestore_client().collection("users")\
                .where("company_id", "==", company_id).stream():
            user_data = _.to_dict()
            
            if rol and user_data.get("rol") != rol:
                continue
            
            total += 1
        
        # Get paginated users with filters
        usuarios = []
        count = 0
        skipped = 0
        
        for doc in get_firestore_client().collection("users")\
                .where("company_id", "==", company_id).stream():
            user_data = doc.to_dict()
            
            if rol and user_data.get("rol") != rol:
                continue
            
            # Apply skip
            if skipped < skip:
                skipped += 1
                continue
            
            # Apply limit
            if count >= limit:
                break
            
            usuarios.append(UsuarioOut(
                uid=doc.id,
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
        
        return PaginacionResponse(
            data=usuarios,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios por compañía: {str(e)}"
        )

@router.get("/{uid}", response_model=UsuarioOut, dependencies=[Depends(require_role("superAdmin", "operativo", "cliente"))])
async def get_usuario(
    uid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener un usuario específico por UID desde Firebase.
    superAdmin, operativo y cliente pueden acceder.
    """
    try:
        doc = get_firestore_client().collection("users").document(uid).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_data = doc.to_dict()
        
        return UsuarioOut(
            uid=doc.id,
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
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )


