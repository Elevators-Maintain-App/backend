from app.db.models.compania import Compania
from app.schemas.compania import CompaniaOut

def compania_to_compania_out(compania: Compania) -> CompaniaOut:
    return CompaniaOut(        
        id=compania.id,
        nombre=compania.nombre,
        documento=compania.documento,
        email=compania.email,
        telefono=compania.telefono,
        pais_id=compania.pais_id,
        nombre_pais=compania.pais.nombre,
        ciudad=compania.ciudad,
        direccion=compania.direccion,
        logo=compania.logo,
        tipo_documento_id=compania.tipo_documento_id,
        tipo_documento_nombre=compania.document_type.nombre,
        created_at=compania.created_at,
        updated_at=compania.updated_at
    )