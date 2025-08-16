# app/services/firebase_storage/firebase_storage.py

import os
from firebase_admin import storage
from uuid import uuid4
from datetime import datetime

def subir_pdf_a_storage(pdf_bytes: bytes, orden_id: str, tipo: str = "prereporte") -> str:
    """
    Sube un archivo PDF a Firebase Storage y devuelve la URL pública.

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
