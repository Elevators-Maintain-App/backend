from typing import List
from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioOut

def usuario_to_usuario_out(usuario: Usuario) -> UsuarioOut:
    return UsuarioOut(
        id=usuario.id,
        company_id=usuario.company_id,
        company_name=usuario.company.nombre,
        display_name=usuario.display_name,
        document_id=usuario.document_id,
        document_type_id=usuario.document_type_id,
        document_type_name=usuario.document_type.nombre,
        email=usuario.email,
        phone_number=usuario.phone_number,
        rol=usuario.rol,
        nivel=usuario.nivel if usuario.nivel else None,
        zona_geografica_id=usuario.zona_geografica_id if usuario.zona_geografica_id else None,
        photo_url=usuario.photo_url if usuario.photo_url else None,
        is_active=usuario.is_active,
        uid=usuario.uid,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at if usuario.updated_at else None,
    )

def usuarios_to_usuarios_out(usuarios: List[Usuario]) -> List[UsuarioOut]:
    return [usuario_to_usuario_out(usuario) for usuario in usuarios]