# app/auth/firebase_admin.py

import firebase_admin
from firebase_admin import credentials
import os
from pathlib import Path

firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

default_path = Path("firebase-service-account.json")

if firebase_json and not default_path.exists():
    with open(default_path, "w") as f:
        f.write(firebase_json)
        
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", default_path)

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)
