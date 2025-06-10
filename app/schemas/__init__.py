# app/schemas/__init__.py

from app.schemas.checklists import ChecklistBase, ChecklistCreate, ChecklistUpdate, ChecklistInDBBase
from app.schemas.clientes import ClienteBase, ClienteCreate, ClienteUpdate, ClienteSchema
from app.schemas.evidencias_multimedia import EvidenciaMultimediaBase, EvidenciaMultimediaCreate, EvidenciaMultimediaUpdate, EvidenciaMultimediaInDBBase
from app.schemas.hojas_de_vida import HojaDeVidaBase, HojaDeVidaCreate, HojaDeVidaUpdate, HojaDeVidaInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoBase, OrdenDeTrabajoCreate, OrdenDeTrabajoUpdate, OrdenDeTrabajoInDBBase
from app.schemas.proyectos import ProyectoBase, ProyectoCreate, ProyectoUpdate, ProyectoInDBBase
from app.schemas.unidades import UnidadBase, UnidadCreate, UnidadUpdate, UnidadInDBBase
from app.schemas.zonas_geograficas import ZonaGeograficaBase, ZonaGeograficaCreate, ZonaGeograficaUpdate, ZonaGeograficaInDBBase
from app.schemas.usuarios import UsuarioBase, UsuarioCreate, UsuarioUpdate, UsuarioInDBBase

from app.schemas.estados_orden import EstadoOrdenBase, EstadoOrdenCreate, EstadoOrdenUpdate, EstadoOrdenInDBBase
from app.schemas.prioridades import PrioridadBase, PrioridadCreate, PrioridadUpdate, PrioridadInDBBase
from app.schemas.tipos_documento import TipoDocumentoBase, TipoDocumentoCreate, TipoDocumentoUpdate, TipoDocumentoInDBBase
from app.schemas.tipos_evidencia import TipoEvidenciaBase, TipoEvidenciaCreate, TipoEvidenciaUpdate, TipoEvidenciaInDBBase
from app.schemas.tipos_orden import TipoOrdenBase, TipoOrdenCreate, TipoOrdenUpdate, TipoOrdenInDBBase
from app.schemas.tipos_unidad import TipoUnidadBase, TipoUnidadCreate, TipoUnidadUpdate, TipoUnidadInDBBase
from app.schemas.comunes import LovElemento
from app.schemas.nivel_tecnico import NivelTecnicoCreate, NivelTecnicoUpdate

__all__ = [
    "ChecklistBase", "ChecklistCreate", "ChecklistUpdate", "ChecklistInDBBase",
    "ClienteBase", "ClienteCreate", "ClienteUpdate", "ClienteSchema",
    "EvidenciaMultimediaBase", "EvidenciaMultimediaCreate", "EvidenciaMultimediaUpdate", "EvidenciaMultimediaInDBBase",
    "HojaDeVidaBase", "HojaDeVidaCreate", "HojaDeVidaUpdate", "HojaDeVidaInDBBase",
    "OrdenDeTrabajoBase", "OrdenDeTrabajoCreate", "OrdenDeTrabajoUpdate", "OrdenDeTrabajoInDBBase",
    "ProyectoBase", "ProyectoCreate", "ProyectoUpdate", "ProyectoInDBBase",
    "UnidadBase", "UnidadCreate", "UnidadUpdate", "UnidadInDBBase",
    "ZonaGeograficaBase", "ZonaGeograficaCreate", "ZonaGeograficaUpdate", "ZonaGeograficaInDBBase",
    "EstadoOrdenBase", "EstadoOrdenCreate", "EstadoOrdenUpdate", "EstadoOrdenInDBBase",
    "PrioridadBase", "PrioridadCreate", "PrioridadUpdate", "PrioridadInDBBase",
    "TipoDocumentoBase", "TipoDocumentoCreate", "TipoDocumentoUpdate", "TipoDocumentoInDBBase",
    "TipoEvidenciaBase", "TipoEvidenciaCreate", "TipoEvidenciaUpdate", "TipoEvidenciaInDBBase",
    "TipoOrdenBase", "TipoOrdenCreate", "TipoOrdenUpdate", "TipoOrdenInDBBase",
    "TipoUnidadBase", "TipoUnidadCreate", "TipoUnidadUpdate", "TipoUnidadInDBBase",
    "UsuarioBase", "UsuarioCreate", "UsuarioUpdate", "UsuarioInDBBase",
    "LovElemento", "NivelTecnicoCreate", "NivelTecnicoUpdate"
]
