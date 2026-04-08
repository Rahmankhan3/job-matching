from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_candidate
from app.models.candidate_profile import CandidateProfile, CandidateProfileUpdate
from app.models.user import User
from app.services.profile_service import get_candidate_profile, upsert_candidate_profile


router = APIRouter(
    prefix="/candidate",
    tags=["Candidate"],
)


@router.get("/profile", response_model=Optional[CandidateProfile])
async def get_profile(
    current_user: Annotated[User, Depends(get_current_candidate)],
):
    """
    Returns the authenticated candidate's full profile.
    Returns null if profile has not been created yet.
    """
    return await get_candidate_profile(current_user.id)


@router.put("/profile", response_model=CandidateProfile)
async def update_profile(
    profile_data: CandidateProfileUpdate,
    current_user: Annotated[User, Depends(get_current_candidate)],
):
    """
    Create or update the candidate's profile.
    Works as an upsert — safe to call even if no profile exists yet.
    """
    updated = await upsert_candidate_profile(
        current_user.id,
        profile_data.model_dump(exclude_none=True)
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )

    return updated