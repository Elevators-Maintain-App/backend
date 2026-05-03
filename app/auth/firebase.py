# app/auth/firebase.py

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth, firestore
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging
from app.db.session import get_db
from app.db.repositories.usuarios import usuario_crud
from app.db.models.usuarios import Usuario
from app.db.models.usuarios import Rol
from uuid import UUID
import string
import secrets

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingrese su token JWT"
)

# Lazy-loaded Firestore client
_db_firestore = None

def get_firestore_client():
    """
    Get Firestore client with lazy initialization.
    This ensures Firebase is initialized before creating the client.
    """
    global _db_firestore
    if _db_firestore is None:
        try:
            _db_firestore = firestore.client()
        except ValueError as e:
            if "does not exist" in str(e):
                logger.error("Firebase not initialized. Make sure initialize_app() is called in main.py")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Firebase no está inicializado"
                )
            raise
    return _db_firestore

class UsuarioFirebaseCreate(BaseModel):
    company_id: UUID | None = None
    company_name: str | None = None
    client_id: UUID | None = None
    client_name: str | None = None
    display_name: str
    document_id: str | None = None
    document_type: str | None = None
    document_type_name: str | None = None
    email: str
    photo_url: Optional[str] = None
    rol: Rol
    password: Optional[str] = None

class FirebaseUser(UsuarioFirebaseCreate):
    uid: str
    created_time: datetime

   
class FirebaseUserCreationError(Exception):
    """Custom exception for Firebase user creation errors"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

async def crear_usuario_firebase(usuario_dto: UsuarioFirebaseCreate, password: Optional[str] = None) -> FirebaseUser:
    """
    Creates a new user in Firebase Auth and stores user data in Firestore.
    
    Args:
        usuario_dto: User data to create
        password: Optional password. If not provided, user will need to set password via email
        
    Returns:
        FirebaseUser: Created user information
        
    Raises:
        FirebaseUserCreationError: If user creation fails
        HTTPException: For validation or permission errors
    """
    try:
        contraseña_temporal = obtener_contraseña_temporal(length=8)
        kwargs = {
            "email": usuario_dto.email,
            "display_name": usuario_dto.display_name,
            "photo_url": usuario_dto.photo_url,
            "password": contraseña_temporal,
            "email_verified": False,
            "disabled": False,
        }
        if password:
            kwargs["password"] = password

        firebase_user = firebase_auth.create_user(**kwargs)
        
        usuario_firestore_data = {
            "uid": firebase_user.uid,
            "company_id": str(usuario_dto.company_id),  # Convert UUID to string
            "company_name": usuario_dto.company_name,
            "display_name": usuario_dto.display_name,
            "document_id": str(usuario_dto.document_id),
            "document_type": usuario_dto.document_type,
            "document_type_name": usuario_dto.document_type_name,
            "email": usuario_dto.email,
            "photo_url": usuario_dto.photo_url,
            "rol": usuario_dto.rol.value if hasattr(usuario_dto.rol, 'value') else str(usuario_dto.rol),
            "client_id": str(usuario_dto.client_id) if usuario_dto.client_id else None,
            "client_name": usuario_dto.client_name,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        get_firestore_client().collection("users").document(firebase_user.uid).set(usuario_firestore_data)
        
        return FirebaseUser(
            uid=firebase_user.uid,
            email=firebase_user.email,
            display_name=firebase_user.display_name,
            created_time=datetime.now(timezone.utc),
            company_id=usuario_dto.company_id,
            company_name=usuario_dto.company_name,
            document_id=usuario_dto.document_id,
            document_type=usuario_dto.document_type,
            document_type_name=usuario_dto.document_type_name,
            password=contraseña_temporal,
            photo_url=usuario_dto.photo_url,
            rol=usuario_dto.rol,
            client_id=usuario_dto.client_id,
            client_name=usuario_dto.client_name,
        )
        
    except firebase_auth.EmailAlreadyExistsError as e:
        raise FirebaseUserCreationError(
            message=f"El usuario con el email {usuario_dto.email} ya existe",
            error_code="EMAIL_ALREADY_EXISTS"
        )    
    except Exception as e:
        if 'firebase_user' in locals():
            try:
                firebase_auth.delete_user(firebase_user.uid)
            except Exception as cleanup_error:
                print(f"Error al eliminar el usuario {firebase_user.uid}: {str(cleanup_error)}")
        raise FirebaseUserCreationError(
            message=f"Error al crear el usuario: {str(e)}",
            error_code="USER_CREATION_FAILED"
        )

async def eliminar_usuario_firebase(uid: str) -> bool:
    """
    Deletes a user from both Firebase Auth and Firestore.
    
    Args:
        uid: Firebase user UID to delete
        
    Returns:
        bool: True if deletion was successful
        
    Raises:
        FirebaseUserCreationError: If deletion fails
    """
    try:
        firebase_auth.delete_user(uid)
        get_firestore_client().collection("users").document(uid).delete()
        return True
        
    except firebase_auth.UserNotFoundError:
        raise FirebaseUserCreationError(
            message=f"El usuario con el UID {uid} no existe",
            error_code="USER_NOT_FOUND"
        )
    except Exception as e:
        raise FirebaseUserCreationError(
            message=f"Error al eliminar el usuario: {str(e)}",
            error_code="USER_DELETION_FAILED"
        )

async def actualizar_usuario_firestore(uid: str, data: dict) -> bool:
    """
    Updates user data in Firestore.
    
    Args:
        uid: Firebase user UID
        data: Data to update
        
    Returns:
        bool: True if update was successful
    """
    try:
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        get_firestore_client().collection("users").document(uid).update(data)
        return True
        
    except Exception as e:
        raise FirebaseUserCreationError(
            message=f"Error al actualizar el usuario: {str(e)}",
            error_code="USER_UPDATE_FAILED"
        )

async def get_current_firebase_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> FirebaseUser:
    """
    Verifica el token Firebase y devuelve el usuario autenticado desde la base de datos.
    """
    token = credentials.credentials

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token.get("uid")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Leer de Firestore
    try:
        doc = get_firestore_client().collection("users").document(uid).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado en Firestore"
            )
        
        data = doc.to_dict()

        # ───── 1. Manejo robusto de company_id ─────
        company_id_str = data.get("company_id")
        try:
            company_id = UUID(company_id_str) if company_id_str else None
        except (ValueError, TypeError):
            company_id = None
        
        current_user = FirebaseUser(
            uid=uid,
            display_name=data.get("display_name", ""),
            email=data.get("email", ""),
            company_id=company_id,
            company_name=data.get("company_name", ""),
            document_id=data.get("document_id", ""),
            document_type=data.get("document_type", ""),
            document_type_name=data.get("document_type_name", ""),
            photo_url=data.get("photo_url"),
            rol=data.get("rol", ""),
            created_time=data.get("created_at", datetime.now())
        )
        request.state.current_user = current_user
        return current_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el usuario: {str(e)}"
        )

def require_role(*allowed_roles: str):
    """
    Dependencia que valida que el usuario autenticado tenga uno de los roles permitidos.
    """
    async def role_dependency(
        current_user: FirebaseUser = Depends(get_current_firebase_user)
    ) -> FirebaseUser:
        if current_user.rol.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Requiere rol: {allowed_roles}"
            )
        return current_user

    return role_dependency

def obtener_contraseña_temporal(length: int = 12) -> str:
        alphabet = (
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + "!@#$%&*"  # Símbolos básicos, evitando caracteres problemáticos
        )
        
        # Generar contraseña aleatoria segura
        return ''.join(secrets.choice(alphabet) for _ in range(length))
