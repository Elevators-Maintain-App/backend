# app/auth/firebase.py

from fastapi import Request, HTTPException, status, Depends
from firebase_admin import auth as firebase_auth, firestore
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.repositories.usuarios import usuario_crud
from app.db.models.usuarios import Usuario


# Cliente de Firestore
db_firestore = firestore.client()

class FirebaseUser(BaseModel):
    uid: str
    display_name: str
    email: str
    company_id: str
    role: str

async def get_current_firebase_user(
    request: Request
) -> FirebaseUser:
    """
    Verifica el token Firebase y devuelve el usuario autenticado desde la base de datos.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    token = auth_header.split(" ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token.get("uid")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Leer de Firestore
    doc = db_firestore.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(404, "Usuario no encontrado en Firestore")

    data = doc.to_dict()
    return FirebaseUser(
        uid=uid,
        display_name=data.get("display_name", ""),
        email=data.get("email", ""),
        company_id=data.get("company_id", ""),
        role=data.get("rol", "")  
    )

def require_role(*allowed_roles: str):
    """
    Dependencia que valida que el usuario autenticado tenga uno de los roles permitidos.
    """
    async def role_dependency(
        current_user: Usuario = Depends(get_current_firebase_user)
    ) -> Usuario:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Requiere rol: {allowed_roles}"
            )
        return current_user

    return role_dependency
