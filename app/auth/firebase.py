# app/auth/firebase.py

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth, firestore
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.repositories.usuarios import usuario_crud
from app.db.models.usuarios import Usuario

# Security scheme
security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter your JWT token"
)

# Cliente de Firestore
db_firestore = firestore.client()

class FirebaseUser(BaseModel):
    uid: str
    display_name: str
    email: str
    company_id: str
    role: str

async def get_current_firebase_user(
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
        doc = db_firestore.collection("users").document(uid).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado en Firestore"
            )
        
        data = doc.to_dict()
        
        return FirebaseUser(
            uid=uid,
            display_name=data.get("display_name", ""),
            email=data.get("email", ""),
            company_id=data.get("company_id", ""),
            role=data.get("rol", "")  
        )
    except Exception as e:
        print(f"❌ Firestore error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing user data: {str(e)}"
        )

def require_role(*allowed_roles: str):
    """
    Dependencia que valida que el usuario autenticado tenga uno de los roles permitidos.
    """
    async def role_dependency(
        current_user: FirebaseUser = Depends(get_current_firebase_user)
    ) -> FirebaseUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Requiere rol: {allowed_roles}"
            )
        return current_user

    return role_dependency
