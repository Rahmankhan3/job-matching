"""
Ranking API routes for recruiter-side ranked candidate views.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from bson import ObjectId

from app.middleware.auth_middleware import get_current_recruiter
from app.models.user import User
from app.models.ranking import CandidateRankingSummary, RankingAnalysisResponse
from app.database import jobs_collection, applications_collection, users_collection, candidate_profiles_collection, parsed_resumes_collection
from app.services.ranking_service import reprocess_application, reprocess_job_applications

router = APIRouter(prefix="/ranking", tags=["Ranking"])


@router.get("/job/{job_id}", response_model=List[CandidateRankingSummary])
async def get_ranked_applications(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Get all applications for a job ranked by AI match score (descending)."""
    try:
        job_oid = ObjectId(job_id)
        job = await jobs_collection.find_one({
            "_id": job_oid,
            "recruiter_id": current_user.id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")

    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")

    cursor = applications_collection.find(
        {"job_posting_id": job_id}
    ).sort("final_match_score", -1) 

    app_list = []
    rank = 1
    async for app in cursor:
        app_data = dict(app)
        app_data["id"] = str(app_data.pop("_id"))

        candidate_email = None
        candidate_name = None
        
        try:
            candidate = await users_collection.find_one(
                {"_id": ObjectId(app_data["candidate_id"])},
                {"email": 1}
            )
            if candidate:
                candidate_email = candidate.get("email")
            
            profile = await candidate_profiles_collection.find_one(
                {"user_id": app_data["candidate_id"]},
                {"full_name": 1}
            )
            if profile:
                candidate_name = profile.get("full_name")
        except Exception:
            pass

        app_list.append(CandidateRankingSummary(
            id=app_data["id"],
            candidate_id=app_data["candidate_id"],
            candidate_email=candidate_email,
            candidate_name=candidate_name,
            resume_url=app_data.get("resume_url"),
            status=app_data.get("status"),
            applied_date=app_data.get("applied_date"),
            final_match_score=app_data.get("final_match_score"),
            matched_skills=app_data.get("matched_skills", []),
            missing_skills=app_data.get("missing_skills", []),
            eligibility_status=app_data.get("eligibility_status"),
            ranking_status=app_data.get("ranking_status"),
            ranking_metadata=app_data.get("ranking_metadata"),
            rank=rank
        ))
        rank += 1

    return app_list


@router.get("/application/{app_id}/analysis", response_model=RankingAnalysisResponse)
async def get_match_analysis(
    app_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Get detailed AI match analysis for a single application."""
    try:
        app_oid = ObjectId(app_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = await applications_collection.find_one({"_id": app_oid})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify recruiter owns the job
    try:
        job = await jobs_collection.find_one({
            "_id": ObjectId(app["job_posting_id"]),
            "recruiter_id": current_user.id,
        })
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied")

    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
        
    candidate_email = None
    candidate_name = None
    try:
        candidate = await users_collection.find_one({"_id": ObjectId(app["candidate_id"])})
        if candidate:
            candidate_email = candidate.get("email")
        
        profile = await candidate_profiles_collection.find_one({"user_id": app["candidate_id"]})
        if profile:
            candidate_name = profile.get("full_name")
    except Exception:
        pass

    # Retrieve parsed resume data from application or fallback to parsed_resumes collection
    parsed_data = app.get("parsed_resume_data")
    if not parsed_data:
        parsed_doc = await parsed_resumes_collection.find_one({"candidate_id": app["candidate_id"]})
        if parsed_doc:
            parsed_data = parsed_doc.get("parsed_data")

    return RankingAnalysisResponse(
        application_id=str(app["_id"]),
        candidate_id=app["candidate_id"],
        candidate_email=candidate_email,
        candidate_name=candidate_name,
        resume_url=app.get("resume_url"),
        cover_letter=app.get("cover_letter"),
        baseline_responses=app.get("baseline_responses"),
        form_responses=app.get("form_responses"),
        parsed_resume_data=parsed_data,
        match_scores=app.get("match_scores"),
        final_match_score=app.get("final_match_score"),
        matched_skills=app.get("matched_skills", []),
        missing_skills=app.get("missing_skills", []),
        eligibility_status=app.get("eligibility_status"),
        ranking_status=app.get("ranking_status"),
        ranking_metadata=app.get("ranking_metadata"),
        ranking_model_version=app.get("ranking_model_version"),
        ranking_updated_at=app.get("ranking_updated_at"),
        status=app.get("status"),
        applied_date=app.get("applied_date"),
        job_title=job.get("title"),
        company=job.get("company"),
    )


@router.post("/application/{app_id}/reprocess")
async def reprocess_single_application(
    app_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Reprocess the ranking for a single application."""
    try:
        app_oid = ObjectId(app_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = await applications_collection.find_one({"_id": app_oid})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = await jobs_collection.find_one({
        "_id": ObjectId(app["job_posting_id"]),
        "recruiter_id": current_user.id,
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
        
    success = await reprocess_application(app_id)
    if not success:
        raise HTTPException(status_code=500, detail="Reprocessing failed")
        
    return {"status": "success", "message": "Application reprocessed successfully"}


@router.post("/job/{job_id}/reprocess")
async def reprocess_all_job_applications(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_recruiter)],
):
    """Reprocess rankings for all applications of a job."""
    try:
        job_oid = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")

    job = await jobs_collection.find_one({
        "_id": job_oid,
        "recruiter_id": current_user.id,
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
        
    count = await reprocess_job_applications(job_id)
    
    return {"status": "success", "reprocessed_count": count}
