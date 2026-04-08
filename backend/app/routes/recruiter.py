from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_recruiter
from app.models.recruiter_profile import RecruiterProfile, RecruiterProfileUpdate
from app.models.user import User
from app.services.profile_service import get_recruiter_profile, upsert_recruiter_profile


router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"],
)


@router.get("/profile", response_model=Optional[RecruiterProfile])
async def get_profile(
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """
    Returns the authenticated recruiter's full company profile.
    Returns null if profile has not been created yet.
    """
    return await get_recruiter_profile(current_user.id)


@router.put("/profile", response_model=RecruiterProfile)
async def update_profile(
    profile_data: RecruiterProfileUpdate,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """
    Create or update the recruiter's company profile.
    Works as an upsert — safe to call even if no profile exists yet.
    """
    updated = await upsert_recruiter_profile(
        current_user.id,
        profile_data.model_dump(exclude_none=True)
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )

    return updated