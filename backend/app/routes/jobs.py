from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.models.job import JobPosting, JobPostingCreate, JobPostingUpdate
from app.models.user import User
from app.database import jobs_collection, applications_collection, recruiter_profiles_collection
from app.services.job_service import (
    create_job_posting,
    get_job_by_id,
    get_jobs_by_recruiter,
    get_all_active_jobs,
    update_job_posting,
    deactivate_job,
)
from app.middleware.auth_middleware import (
    get_current_recruiter,
    get_optional_user,
)


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/my-jobs", response_model=List[JobPosting])
async def list_my_jobs(
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Get the current recruiter's own job postings."""
    return await get_jobs_by_recruiter(current_user.id)


@router.get("/", response_model=List[JobPosting])
async def list_jobs(limit: int = 50):
    """Get all active job postings (public)."""
    return await get_all_active_jobs(limit)


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user: Annotated[Optional[User], Depends(get_optional_user)] = None
):
    """
    Get a single job by ID (public).
    If authenticated as candidate, returns application tracking info.
    Also returns related jobs.
    """
    job = await get_job_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job_dict = job.model_dump()
    job_dict["has_applied"] = False
    job_dict["user_application"] = None
    job_dict["related_jobs"] = []
    job_dict["company_reviews"] = []

    # Fetch company reviews from recruiter profile
    recruiter_profile = await recruiter_profiles_collection.find_one({"user_id": job.recruiter_id})
    if recruiter_profile and "company_reviews" in recruiter_profile:
        job_dict["company_reviews"] = recruiter_profile["company_reviews"]

    # Fetch related jobs (same company or title)
    cursor = jobs_collection.find({
        "_id": {"$ne": ObjectId(job_id)},
        "is_active": True,
        "$or": [{"title": job.title}, {"company": job.company}]
    }).limit(3)

    related_jobs = []
    async for r_job in cursor:
        r_job["id"] = str(r_job.pop("_id"))
        related_jobs.append(r_job)
    job_dict["related_jobs"] = related_jobs

    if current_user and current_user.role == "candidate":
        app = await applications_collection.find_one({
            "candidate_id": current_user.id,
            "job_posting_id": job_id
        })
        if app:
            job_dict["has_applied"] = True
            app["id"] = str(app.pop("_id"))
            job_dict["user_application"] = app

    return job_dict


@router.post("/", response_model=JobPosting, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobPostingCreate,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Create a new job posting (recruiter only)."""
    job = await create_job_posting(current_user.id, job_data.model_dump())
    if not job:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")
    return job


@router.patch("/{job_id}", response_model=JobPosting)
async def update_job(
    job_id: str,
    job_data: JobPostingUpdate,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Update a job posting (recruiter owner only). Partial updates supported."""
    updates = job_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    updated = await update_job_posting(job_id, current_user.id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or you do not have permission to edit it"
        )
    return updated


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_job(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Close/deactivate a job posting (recruiter owner only)."""
    success = await deactivate_job(job_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or you do not have permission to close it"
        )