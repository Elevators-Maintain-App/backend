from app.db.models.proyectos import Proyecto
from app.schemas.proyectos import ProyectoOut

def map_proyecto_to_proyecto_out(proyecto: Proyecto) -> ProyectoOut:
    return ProyectoOut(
        id=proyecto.id,
        nombre=proyecto.nombre,
        estado=proyecto.estado,
        direccion=proyecto.direccion,
        zona_geografica_id=proyecto.zona_geografica_id,
        cliente_id=proyecto.cliente_id,
        cliente_nombre=proyecto.cliente.nombre if proyecto.cliente else None,
        company_id=proyecto.company_id,
        company_nombre=proyecto.compania.nombre if proyecto.compania else None,
        created_at=proyecto.created_at,
        updated_at=proyecto.updated_at,
    )

