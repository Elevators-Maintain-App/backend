from abc import ABC
from app.auth.firebase import FirebaseUser
from app.schemas.usuarios import UsuarioCreate
from app.db.models.usuarios import Usuario
from app.db.models import Compania, TipoDocumento, Cliente
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
    cliente: Cliente | None

class UsuarioCaseInterface(ABC):
    def obtener_firebase_usuario(self, usuario_nuevo: UsuarioCreate) -> FirebaseUser:
        ...

    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> UsuarioCreate:
        ...

    def validar_y_normalizar_company_id(self, usuario_actual: Usuario, company_id: Optional[UUID]) -> UUID:
        """
        Valida y normaliza el company_id según las reglas del rol del usuario actual.
        Para admin/supervisor: usa su company_id si no se proporciona.
        Para superAdmin: requiere que se proporcione company_id.
        """
        ...

    def obtener_filtros_para_listar_usuarios(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], rol: Optional[str]) -> dict:
        ...

    def obtener_filtro_para_totalizar_usuarios(self, usuario_actual: Usuario, company_id: Optional[UUID], rol: Optional[Rol]) -> dict:
        ...

    async def enviar_email_de_bienvenida(self, email_destinatario: str, nombre_destinatario: str, password: str):
        ...

    async def enviar_email_de_cambio_de_contraseña(self, email_destinatario: str, nombre_destinatario: str):
        ...