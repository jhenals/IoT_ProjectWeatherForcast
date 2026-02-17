from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from app.database import get_session
from app.models import User
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Request model for registration - receives JSON body
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Username (minimum 3 characters)")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")

# Response models
class MessageResponse(BaseModel):
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_session)):
    """
    Register a new user account.
    
    - **username**: Unique username (min 3 characters)
    - **password**: Password (min 6 characters) - will be hashed before storage
    """
    # Check if username already exists
    existing_user = db.exec(select(User).where(User.username == req.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user with hashed password
    new_user = User(
        username=req.username,
        hashed_password=hash_password(req.password)
    )
    db.add(new_user)
    db.commit()
    
    return {"message": "User created successfully"}

@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    Login with username and password.
    
    Returns a JWT access token for authenticated requests.
    """
    # Find user
    user = db.exec(select(User).where(User.username == form.username)).first()
    
    # Verify credentials
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token({"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }