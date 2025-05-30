# app/auth/firebase_admin.py

import firebase_admin
from firebase_admin import credentials
import os
from pathlib import Path
import base64

firebase_json_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_B64")

default_path = Path("firebase-service-account.json")

if firebase_json_b64 and not default_path.exists():
    firebase_json = base64.b64decode(firebase_json_b64).decode("utf-8")
    with open(default_path, "w") as f:
        f.write(firebase_json)

firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", default_path)

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)
