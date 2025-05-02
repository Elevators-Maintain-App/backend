# app/auth/firebase_admin.py

import firebase_admin
from firebase_admin import credentials
import os
from pathlib import Path

# Ruta por defecto (local)
default_path = Path("firebase-service-account.json")

# Ruta alternativa desde variable de entorno
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", default_path)

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)
