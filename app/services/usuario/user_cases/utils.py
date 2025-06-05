from app.auth.firebase import FirebaseUser
from app.schemas.usuarios import UsuarioCreate
from app.db.models.compania import Compania
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.usuarios import Usuario

def mapear_usuario_dto_a_usuario_firebase(usuario_nuevo: UsuarioCreate, compania: Compania, tipo_documento: TipoDocumento) -> FirebaseUser:
    usuario_firebase = FirebaseUser(
            company_id=compania.id,
            company_name=compania.nombre,
            display_name=usuario_nuevo.display_name,
            document_id=usuario_nuevo.document_id,
            document_type=tipo_documento.id,
            document_type_name=tipo_documento.nombre,
            email=usuario_nuevo.email,
            photo_url=usuario_nuevo.photo_url,
            rol=usuario_nuevo.rol,
        )
                
    return usuario_firebase

def mapear_usuario_dto_a_usuario(usuario_nuevo: UsuarioCreate, firebase_uid: str) -> Usuario:
    usuario = Usuario(
                uid=firebase_uid,
                display_name=usuario_nuevo.display_name,
                document_id=usuario_nuevo.document_id,
                document_type_id=usuario_nuevo.document_type_id,
                email=usuario_nuevo.email,
                phone_number=usuario_nuevo.phone_number,
                photo_url=usuario_nuevo.photo_url,
                rol=usuario_nuevo.rol,
                nivel=usuario_nuevo.nivel,
                zona_geografica_id=usuario_nuevo.zona_geografica_id,
                is_active=usuario_nuevo.is_active,
                company_id=usuario_nuevo.company_id,
            )
    
    return usuario