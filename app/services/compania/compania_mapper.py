from app.db.models.compania import Compania
from app.schemas.compania import CompaniaOut

def compania_to_compania_out(compania: Compania) -> CompaniaOut:
    # Safely extract relationship data
    nombre_pais = None
    try:
        if hasattr(compania, 'pais') and compania.pais is not None:
            nombre_pais = compania.pais.nombre
    except Exception:
        pass  # Relationship not loaded or error accessing it
    
    tipo_documento_nombre = None
    try:
        if hasattr(compania, 'document_type') and compania.document_type is not None:
            tipo_documento_nombre = compania.document_type.nombre
    except Exception:
        pass  # Relationship not loaded or error accessing it
    
    return CompaniaOut(        
        id=compania.id,
        nombre=compania.nombre,
        documento=compania.documento,
        email=compania.email,
        telefono=compania.telefono,
        pais_id=compania.pais_id,
        nombre_pais=nombre_pais,
        ciudad=compania.ciudad,
        direccion=compania.direccion,
        logo=compania.logo,
        tipo_documento_id=compania.tipo_documento_id,
        tipo_documento_nombre=tipo_documento_nombre,
        created_at=compania.created_at,
        updated_at=compania.updated_at
    )