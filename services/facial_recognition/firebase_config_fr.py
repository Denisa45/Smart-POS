import firebase_admin
from firebase_admin import credentials, firestore

# init only once
if not firebase_admin._apps:
    cred = credentials.Certificate(
        r"C:\Users\DELL\Desktop\Facultate\iot-kiosk-project\serviceAccountKey.json"
    )
    firebase_admin.initialize_app(cred)

db = firestore.client()