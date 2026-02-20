import firebase_admin
from firebase_admin import credentials, auth, firestore
import os


def init_firebase():
    cred_dict = {'C:/Users/subol/Desktop/LM Telecom Engineering/IOT/projects/smart-park-iot/important/smart-park-iot-d7743-firebase-adminsdk-fbsvc-2938d538d4.json'}
    cred = credentials.Certificate(cred_dict)
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
