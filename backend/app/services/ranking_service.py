"""
Ranking orchestration service.

Handles the end-to-end pipeline: parsing -> embedding -> matching -> storing.
Maintains clean separation of concerns by delegating specific tasks to
the parser, embedding service, and matching engine.
"""
import os
import logging
from datetime import datetime
from bson import ObjectId

from app.database import applications_collection, jobs_collection, parsed_resumes_collection
from app.models.ranking import RankingStatus
from app.config import settings
from app.services.resume_parser import parse_resume_to_dict
from app.services.matching_engine import compute_match_score

logger = logging.getLogger(__name__)


async def _get_or_create_parsed_resume(candidate_id: str, resume_url: str, force_reparse: bool = False) -> dict:
    """
    Fetch the parsed resume from the database, or parse it if not found, updated, or forced.
    Reuses parsed resume representation across applications for the same candidate.
    """
    if not force_reparse:
        existing = await parsed_resumes_collection.find_one({"candidate_id": candidate_id})
        # Check if we have cached data and it matches the current resume URL
        if existing and existing.get("parsed_data"):
            cached_url = existing.get("resume_url")
            if not resume_url or cached_url == resume_url:
                logger.info(f"Reusing cached parsed resume for candidate {candidate_id}")
                return existing["parsed_data"]

    # Not cached or resume file changed — parse the resume file
    file_path = None
    if resume_url and "uploads/resumes/" in resume_url:
        filename = resume_url.split("uploads/resumes/")[-1].split("?")[0].split("#")[0]
        file_path = os.path.join(
            os.path.dirname(__file__), "..", "uploads", "resumes", filename
        )
        file_path = os.path.normpath(file_path)
    elif resume_url and os.path.isabs(resume_url) and os.path.isfile(resume_url):
        file_path = resume_url

    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError(f"Resume file not found: {resume_url}")

    parsed_data = parse_resume_to_dict(file_path)
    if not parsed_data:
        raise ValueError("Resume parsing returned no data (possibly empty or corrupt)")

    # Store in parsed_resumes collection for reusable access across applications
    await parsed_resumes_collection.update_one(
        {"candidate_id": candidate_id},
        {
            "$set": {
                "parsed_data": parsed_data,
                "resume_url": resume_url,
                "parser_version": settings.PARSER_VERSION,
                "parsed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return parsed_data


async def process_application_ranking(
    application_id: str,
    candidate_id: str,
    resume_url: str,
    job_doc: dict,
    form_responses: dict,
    cover_letter: str = None,
    force_reparse: bool = False
) -> bool:
    """
    Run the end-to-end AI ranking pipeline for a single application.
    Updates the application document in MongoDB with the results.
    """
    app_oid = ObjectId(application_id)
    
    try:
        # 1. Set status to processing
        await applications_collection.update_one(
            {"_id": app_oid},
            {"$set": {"ranking_status": RankingStatus.processing.value}}
        )

        # 2. Get parsed resume (reuses existing if possible, or forces re-parse)
        parsed_resume = await _get_or_create_parsed_resume(candidate_id, resume_url, force_reparse=force_reparse)

        # 3. Compute match scores (this implicitly handles embeddings)
        match_result = compute_match_score(
            job_data=job_doc,
            parsed_resume=parsed_resume,
            form_responses=form_responses or {},
            cover_letter=cover_letter
        )

        # 4. Store results
        await applications_collection.update_one(
            {"_id": app_oid},
            {
                "$set": {
                    "parsed_resume_data": parsed_resume,
                    "match_scores": match_result["scores"],
                    "final_match_score": match_result["final_score"],
                    "matched_skills": match_result["matched_skills"],
                    "missing_skills": match_result["missing_skills"],
                    "eligibility_status": match_result["eligibility_status"],
                    "ranking_metadata": match_result["ranking_metadata"],
                    "ranking_status": RankingStatus.completed.value,
                    "ranking_model_version": settings.RANKING_MODEL_VERSION,
                    "ranking_updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"AI ranking completed: app={application_id}, score={match_result['final_score']}")
        return True

    except Exception as e:
        logger.error(f"AI ranking failed for app {application_id}: {e}", exc_info=True)
        # Mark as failed so the recruiter knows why there's no score
        await applications_collection.update_one(
            {"_id": app_oid},
            {
                "$set": {
                    "ranking_status": RankingStatus.failed.value,
                    "ranking_metadata": {"error": str(e)}
                }
            }
        )
        return False


async def reprocess_application(application_id: str, force_reparse: bool = False) -> bool:
    """Manually trigger a re-ranking for a specific application."""
    app_oid = ObjectId(application_id)
    app = await applications_collection.find_one({"_id": app_oid})
    if not app:
        return False
        
    job = await jobs_collection.find_one({"_id": ObjectId(app["job_posting_id"])})
    if not job:
        return False
        
    return await process_application_ranking(
        application_id=str(app["_id"]),
        candidate_id=app["candidate_id"],
        resume_url=app.get("resume_url"),
        job_doc=job,
        form_responses=app.get("form_responses", {}),
        cover_letter=app.get("cover_letter"),
        force_reparse=force_reparse
    )


async def reprocess_job_applications(job_id: str) -> int:
    """
    Re-rank all applications for a job (e.g., when JD changes).
    Returns the number of successfully reprocessed applications.
    """
    job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return 0
        
    cursor = applications_collection.find({"job_posting_id": job_id})
    success_count = 0
    
    async for app in cursor:
        success = await process_application_ranking(
            application_id=str(app["_id"]),
            candidate_id=app["candidate_id"],
            resume_url=app.get("resume_url"),
            job_doc=job,
            form_responses=app.get("form_responses", {}),
            cover_letter=app.get("cover_letter")
        )
        if success:
            success_count += 1
            
    return success_count
