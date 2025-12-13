# app/services/firebase_storage/firebase_storage.py

import os
from firebase_admin import storage
from uuid import uuid4
from datetime import datetime
from typing import Optional
from uuid import UUID


def subir_archivo_a_storage(
    archivo_bytes: bytes,
    compania_id: Optional[UUID],
    entidad: str,
    entidad_id: Optional[UUID],
    nombre_archivo: str,
    tipo_archivo: str,
    content_type: str
) -> str:
    """
    Función genérica para subir cualquier tipo de archivo a Firebase Storage.
    
    Estructura del bucket:
    - /companies/{compania_id}/{entidad}/{entidad_id}/{tipo_archivo}/{nombre_archivo}
    - Si compania_id es None: /{entidad}/{entidad_id}/{tipo_archivo}/{nombre_archivo}
    - Si entidad_id es None: /companies/{compania_id}/{entidad}/{tipo_archivo}/{nombre_archivo}
    
    Args:
        archivo_bytes: contenido binario del archivo.
        compania_id: UUID de la compañía (opcional).
        entidad: tipo de entidad (ej: "clients", "companies", "orders").
        entidad_id: UUID de la entidad (opcional).
        nombre_archivo: nombre descriptivo del archivo (se añadirá UUID único).
        tipo_archivo: tipo de archivo (ej: "logo", "evidencia", "documento", "reporte").
        content_type: tipo MIME del archivo (ej: "image/jpeg", "application/pdf").
    
    Returns:
        str: URL pública del archivo subido.
    
    Ejemplos:
        # Logo de cliente
        subir_archivo_a_storage(
            archivo_bytes=logo_bytes,
            compania_id=UUID("..."),
            entidad="clients",
            entidad_id=UUID("..."),
            nombre_archivo="logo",
            tipo_archivo="logo",
            content_type="image/jpeg"
        )
        
        # Logo de compañía
        subir_archivo_a_storage(
            archivo_bytes=logo_bytes,
            compania_id=UUID("..."),
            entidad="companies",
            entidad_id=UUID("..."),
            nombre_archivo="logo",
            tipo_archivo="logo",
            content_type="image/png"
        )
        
        # Documento de orden
        subir_archivo_a_storage(
            archivo_bytes=doc_bytes,
            compania_id=UUID("..."),
            entidad="orders",
            entidad_id=UUID("..."),
            nombre_archivo="reporte",
            tipo_archivo="documento",
            content_type="application/pdf"
        )
    """
    bucket = storage.bucket()
    # Construir ruta del archivo
    partes_ruta = []
    
    if compania_id:
        partes_ruta.append(f"companies/{compania_id}")
    
    partes_ruta.append(entidad)
    
    if entidad_id:
        partes_ruta.append(str(entidad_id))
    
    partes_ruta.append(tipo_archivo)

    extension = _obtener_extension_por_content_type(content_type)
    uuid_unico = uuid4().hex[:8]

    nombre_completo = f"{nombre_archivo}_{uuid_unico}{extension}"
    partes_ruta.append(nombre_completo)
    
    ruta_completa = "/".join(partes_ruta)

    blob = bucket.blob(ruta_completa)
    blob.upload_from_string(archivo_bytes, content_type=content_type)
    blob.make_public()

    return blob.public_url


def subir_pdf_a_storage(pdf_bytes: bytes, orden_id: str, tipo: str = "prereporte") -> str:
    """
    Sube un archivo PDF a Firebase Storage y devuelve la URL pública.
    
    Esta función mantiene compatibilidad con código existente.
    Para nuevos desarrollos, usar subir_archivo_a_storage directamente.

    Args:
        pdf_bytes: contenido binario del archivo PDF.
        orden_id: UUID de la orden para usar como nombre base del archivo.
        tipo: "prereporte" o "final".

    Returns:
        str: URL pública del archivo subido.
    """
    if tipo not in ["prereporte", "final"]:
        raise ValueError("Tipo inválido. Usa 'prereporte' o 'final'.")

    bucket = storage.bucket()
    nombre_archivo = f"reportes/{tipo}s/reporte_{orden_id}_{uuid4().hex[:6]}.pdf"

    blob = bucket.blob(nombre_archivo)
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")
    blob.make_public()

    return blob.public_url


def _obtener_extension_por_content_type(content_type: str) -> str:
    """
    Obtiene la extensión del archivo basado en el content type.
    
    Args:
        content_type: tipo MIME del archivo.
    
    Returns:
        str: extensión del archivo (ej: ".jpg", ".png", ".pdf").
    """
    extensiones = {
        # Imágenes
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
        # Documentos
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-powerpoint": ".ppt",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        # Texto
        "text/plain": ".txt",
        "text/csv": ".csv",
        "text/html": ".html",
        # Otros
        "application/zip": ".zip",
        "application/x-zip-compressed": ".zip",
        "application/json": ".json",
        "application/xml": ".xml",
    }
    return extensiones.get(content_type.lower(), "")
