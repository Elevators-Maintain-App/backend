from app.db.models.clientes import Cliente
from app.schemas.clientes import ClienteOut

def cliente_to_cliente_out(cliente: Cliente) -> ClienteOut:
    return ClienteOut(
        id=cliente.id,
        nombre=cliente.nombre,
        email=cliente.email,
        telefono=cliente.telefono,
        pais_id=cliente.pais_id,
        nombre_pais=cliente.pais.nombre,
        tipo_documento_id=cliente.tipo_documento_id,
        tipo_documento_nombre=cliente.tipos_documento.nombre,
        documento=cliente.documento,
        ciudad=cliente.ciudad,
        direccion=cliente.direccion,
        logo=cliente.logo,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at
    )