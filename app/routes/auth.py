import requests
from typing import Dict, Optional
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import firestore
from pydantic import BaseModel
from app.database import get_firestore_db


class UserLoginRequest(BaseModel):
    email: str
    password: str


router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Firebase-only configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


def get_db():
    return get_firestore_db()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_role: str


def get_firebase_admin_user(credentials=Depends(security)):
    """
    FIREBASE ADMIN ONLY AUTHENTICATION
    Validates Firebase ID token and enforces admin role from Firestore

    This is the ONLY accepted authentication method for all protected endpoints.

    Usage:
    1. Call /api/auth/login with your Firebase email/password to get access token
    2. Use the returned access_token as Bearer token in Authorization header
    3. Token will be validated against Firebase database for admin role
    """
    try:
        # Verify Firebase ID token
        token = credentials.credentials
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token.get("uid")

        # Check user exists and has admin role in Firestore
        user_doc = get_db().collection("users").document(uid).get()

        if not user_doc.exists():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin user not found in database"
            )

        user_data = user_doc.to_dict()

        # STRICT: Only allow users with admin role
        if user_data.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required. Only Firebase admin credentials are accepted."
            )

        return {
            "uid": uid,
            "role": user_data.get("role"),
            "email": user_data.get("email")
        }

    except HTTPException:
        raise
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )


@router.post("/login/firebase", response_model=TokenResponse)
def login_firebase(req: UserLoginRequest):
    """
    Firebase Admin Login Endpoint

    Login with Firebase email and password. User MUST have admin role in Firestore.
    Returns access token to use in protected endpoints.

    Steps:
    1. Enter your Firebase admin email and password
    2. You'll receive an access_token
    3. Use this token as: Authorization: Bearer <access_token>
    4. All protected endpoints will validate your admin role in Firebase
    """
    try:
        # Get user by email
        user = firebase_auth.get_user_by_email(req.email)
        uid = user.uid

        # Verify password using Firebase REST API
        api_key = "AIzaSyAvlmocEGgpWviAtHTcPaoxQWh5PZ6QDbI"

        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={
                "email": req.email,
                "password": req.password,
                "returnSecureToken": True
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        data = response.json()
        access_token = data.get("idToken")

        # Get user role from Firestore and ENFORCE admin role
        user_doc = get_db().collection("users").document(uid).get()

        if not user_doc.exists():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found in admin database"
            )

        user_data = user_doc.to_dict()
        user_role = user_data.get("role", "visitor")

        # Strict admin enforcement
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Firebase admin users can access this API. Your account does not have admin privileges."
            )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_role": user_role
        }

    except HTTPException:
        raise
    except firebase_auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase email not registered"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest):
    """
    Main Firebase Admin Login Endpoint (backward compatible)

    Login with email and password. User MUST have admin role in Firestore.
    This is the only login method supported - all other auth methods are disabled.
    """
    try:
        # Get user by email
        user = firebase_auth.get_user_by_email(req.email)
        uid = user.uid

        # Verify password using Firebase REST API
        api_key = "AIzaSyAvlmocEGgpWviAtHTcPaoxQWh5PZ6QDbI"

        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={
                "email": req.email,
                "password": req.password,
                "returnSecureToken": True
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        data = response.json()
        access_token = data.get("idToken")

        # Get user role from Firestore and ENFORCE admin role
        user_doc = get_db().collection("users").document(uid).get()

        if not user_doc.exists():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found in admin database"
            )

        user_data = user_doc.to_dict()
        user_role = user_data.get("role", "visitor")

        # Strict admin enforcement
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Firebase admin users can access this API. Your account does not have admin privileges."
            )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_role": user_role
        }

    except HTTPException:
        raise
    except firebase_auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase email not registered"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )
