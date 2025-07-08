from abc import ABC
from app.auth.firebase import FirebaseUser
from app.schemas.usuarios import UsuarioCreate
from app.db.models.usuarios import Usuario
from app.db.models import Compania, TipoDocumento
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from app.db.models.usuarios import Rol

@dataclass
class CrearUsuarioParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    firebase_uid: str

@dataclass
class CrearUsuarioFirebaseParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    compania: Compania
    tipo_documento: TipoDocumento
    firebase_uid: str

class UsuarioCaseInterface(ABC):
    def obtener_firebase_usuario(self, usuario_nuevo: UsuarioCreate) -> FirebaseUser:
        ...

    def obtener_usuario_a_guardar(self, usuario_nuevo: UsuarioCreate) -> UsuarioCreate:
        ...

    def obtener_filtros_para_listar_usuarios(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], rol: Optional[str]) -> dict:
        ...

    def obtener_filtro_para_totalizar_usuarios(self, usuario_actual: Usuario, company_id: Optional[UUID], rol: Optional[Rol]) -> dict:
        ...

    async def enviar_email_de_bienvenida(self, email_destinatario: str, nombre_destinatario: str, password: str):
        ...