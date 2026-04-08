from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional

from app.utils.jwt import decode_access_token
from app.services.user_service import get_user_by_id
from app.models.user import UserRole, User


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[User]:
    if not credentials:
        return None
        
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        return None
        
    user_id: str = payload.get("user_id")
    if not user_id:
        return None
        
    user = await get_user_by_id(user_id)
    return user


async def get_current_candidate(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:

    if current_user.role != UserRole.candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required",
        )

    return current_user


async def get_current_recruiter(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:

    if current_user.role != UserRole.recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required",
        )

    return current_user