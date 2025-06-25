from app.schemas.usuarios import UsuarioCreate
from app.db.models.compania import Compania
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.usuarios import Usuario
from app.auth.firebase import UsuarioFirebaseCreate
import uuid

def mapear_usuario_dto_a_usuario_firebase(usuario_nuevo: UsuarioCreate, compania: Compania, tipo_documento: TipoDocumento) -> UsuarioFirebaseCreate:
    usuario_firebase = UsuarioFirebaseCreate(
            company_id=compania.id,
            company_name=compania.nombre,
            display_name=usuario_nuevo.display_name,
            document_id=str(usuario_nuevo.document_id),
            document_type=str(tipo_documento.id),
            document_type_name=tipo_documento.nombre,
            email=usuario_nuevo.email.lower(),
            photo_url= usuario_nuevo.photo_url if usuario_nuevo.photo_url else None,
            rol=usuario_nuevo.rol.value,
        )
                
    return usuario_firebase

def mapear_usuario_dto_a_usuario_create(usuario_nuevo: UsuarioCreate, firebase_uid: str) -> UsuarioCreate:
    usuario = UsuarioCreate(
                uid=firebase_uid,
                display_name=usuario_nuevo.display_name,
                document_id=usuario_nuevo.document_id,
                document_type_id=usuario_nuevo.document_type_id,
                email=usuario_nuevo.email.lower(),
                phone_number=usuario_nuevo.phone_number,
                photo_url=usuario_nuevo.photo_url if usuario_nuevo.photo_url else None,
                rol=usuario_nuevo.rol,
                nivel=usuario_nuevo.nivel if usuario_nuevo.nivel else None,
                zona_geografica_id=usuario_nuevo.zona_geografica_id if usuario_nuevo.zona_geografica_id else None,
                is_active=usuario_nuevo.is_active,
                company_id=usuario_nuevo.company_id,
            )
    
    return usuario