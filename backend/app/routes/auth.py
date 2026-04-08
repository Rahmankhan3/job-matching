from fastapi import APIRouter, HTTPException, status
from typing import Dict

from app.models.user import (
    UserCreate,
    User,
    LoginRequest,
    UserInDB,
    UserRole,
)
from app.services.user_service import create_user, authenticate_user
from app.utils.jwt import create_access_token



router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate) -> User:

    created_user = await create_user(
        email=user_data.email,
        password=user_data.password,
        role=user_data.role.value,   # store as plain string in DB
    )

    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return created_user


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_data: LoginRequest) -> Dict[str, object]:
   
    user: UserInDB | None = await authenticate_user(
        user_data.email,
        user_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,   # store Enum as plain string in token
    }

    access_token = create_access_token(token_payload)

    
    response_user = User(
        id=user.id,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": response_user,
    }
