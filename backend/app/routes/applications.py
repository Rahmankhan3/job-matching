from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.models.application import (
    ApplicationCreate,
    Application,
    ApplicationStatusUpdate,
)
from app.models.application_view import (
    ApplicationRecruiterView,
    ApplicationCandidateView,
)
from app.models.user import User
from app.database import applications_collection, jobs_collection
from app.middleware.auth_middleware import (
    get_current_candidate,
    get_current_recruiter,
)
from app.services.application_service import (
    create_application,
    get_applications_by_candidate,
    get_applications_by_job,
    update_application_status,
    get_application_by_id,
    get_applications_by_candidate_with_job,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post("/", response_model=Application, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    application_data: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_candidate)],
):
    """
    Candidate applies to a job..
    Job existence, activeness, duplicate, and required custom-field checks
    are all handled in the service layer.
    """
    try:
        app = await create_application(
            current_user.id,
            application_data.job_posting_id,
            application_data.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already applied or job not found",
        )

    return app


@router.get(
    "/my-applications",
    response_model=List[ApplicationCandidateView],
)
async def list_my_applications(
    current_user: Annotated[User, Depends(get_current_candidate)],
):
    """
    Candidate sees all their applications with job summaries.
    """

    return await get_applications_by_candidate_with_job(current_user.id)


@router.get("/job/{job_id}", response_model=List[ApplicationRecruiterView])
async def list_applications_by_job(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """
    Recruiter sees all applications for a specific job they own.

    We do two checks:
    1. job_id must be a valid ObjectId format.
    2. Job must exist AND belong to the current recruiter.
    """

    try:
        job_object_id = ObjectId(job_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job = await jobs_collection.find_one(
        {"_id": job_object_id, "recruiter_id": current_user.id}
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or access denied",
        )

    return await get_applications_by_job(job_id)


@router.put("/{application_id}/status", response_model=Application)
async def update_status(
    application_id: str,
    status_update: ApplicationStatusUpdate,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """
    Recruiter updates an application's status.
    Ownership check (recruiter owns the job for this application)
    is done inside update_application_status().
    """

    app = await update_application_status(
        application_id,
        current_user.id,
        status_update.status.value,
        status_update.notes,
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or unauthorized",
        )

    return app