from fastapi import APIRouter, HTTPException, status
from firebase_admin import auth as firebase_auth
from app.models import UserLoginRequest
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest):
    """
    Login with email and password.

    Returns a Firebase ID token for authenticated requests.
    """
    try:
        # Get user by email to retrieve UID
        user = firebase_auth.get_user_by_email(req.email)

        # Verify password using Firebase REST API
        # (Firebase Admin SDK doesn't have built-in password verification)
        import requests
        import os

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
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        data = response.json()
        access_token = data.get("idToken")

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except firebase_auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not registered. Please sign up first.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
