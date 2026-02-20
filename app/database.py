import firebase_admin
from firebase_admin import credentials, auth, firestore
import os

# Initialize Firebase


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "smart-park-iot-d7743",
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", "firebase-adminsdk@smart-park-iot-d7743.iam.gserviceaccount.com"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CERT_URL", "")
        })
        firebase_admin.initialize_app(cred)


def get_firebase_auth():
    """Get Firebase Auth instance"""
    init_firebase()
    return auth


def get_firestore_db():
    """Get Firestore instance"""
    init_firebase()
    return firestore.client()


def create_db():
    """Firebase initialization - collections are created on first write"""
    init_firebase()
