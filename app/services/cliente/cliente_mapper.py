from app.db.models.clientes import Cliente
from app.schemas.clientes import ClienteOut

def cliente_to_cliente_out(cliente: Cliente) -> ClienteOut:
    nombre_pais = None
    try:
        if hasattr(cliente, 'pais') and cliente.pais is not None:
            nombre_pais = cliente.pais.nombre
    except Exception:
        pass  # Relationship not loaded or error accessing it
    
    tipo_documento_nombre = None
    try:
        if hasattr(cliente, 'tipos_documento') and cliente.tipos_documento is not None:
            tipo_documento_nombre = cliente.tipos_documento.nombre
    except Exception:
        pass  # Relationship not loaded or error accessing it
    
    return ClienteOut(
        id=cliente.id,
        nombre=cliente.nombre,
        email=cliente.email,
        telefono=cliente.telefono,
        pais_id=cliente.pais_id,
        nombre_pais=nombre_pais,
        tipo_documento_id=cliente.tipo_documento_id,
        tipo_documento_nombre=tipo_documento_nombre,
        documento=cliente.documento,
        ciudad=cliente.ciudad,
        direccion=cliente.direccion,
        logo=cliente.logo,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
        compania_id=cliente.compania_id
    )