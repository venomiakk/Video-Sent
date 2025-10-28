from fastapi import APIRouter, HTTPException, status
from .schemas import UserCreate, UserLogin, Token, UserResponse
from .service import (
    create_user, 
    authenticate_user, 
    create_access_token
)
from datetime import datetime

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Create user
    user = await create_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": str(user["_id"])}
    )
    
    # Return token and user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "created_at": user["created_at"]
        }
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    # Authenticate user
    user = await authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": str(user["_id"])}
    )
    
    # Return token and user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "created_at": user["created_at"]
        }
    }


@router.get("/test")
def auth_test():
    """Test endpoint"""
    return {"message": "Auth module is UP"}
