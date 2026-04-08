from app.database import jobs_collection
from app.models.job import JobPosting
from typing import List, Optional
from bson import ObjectId
from datetime import datetime


async def create_job_posting(
    recruiter_id: str,
    job_data: dict
) -> Optional[JobPosting]:

    job_doc = {
        **job_data,                              # title, company, location, etc.
        "recruiter_id": recruiter_id,            # injected from JWT, not user input
        "is_active": True,
        "posted_date": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await jobs_collection.insert_one(job_doc)

    if result.inserted_id:
        created_job = await jobs_collection.find_one(
            {"_id": result.inserted_id}
        )
        created_job["id"] = str(created_job.pop("_id"))
        return JobPosting(**created_job)

    return None


async def get_job_by_id(job_id: str) -> Optional[JobPosting]:
 
    try:
        object_id = ObjectId(job_id)
    except Exception:
        return None  # invalid ID format — treat as not found

    job_doc = await jobs_collection.find_one(
        {"_id": object_id, "is_active": True}
    )

    if job_doc:
        job_doc["id"] = str(job_doc.pop("_id"))
        return JobPosting(**job_doc)

    return None


async def get_jobs_by_recruiter(recruiter_id: str) -> List[JobPosting]:

    cursor = jobs_collection.find({
        "recruiter_id": recruiter_id,
        "is_active": True
    })

    job_list = []

    # async for is how you iterate motor cursors — DO NOT use regular for
    async for job in cursor:
        job["id"] = str(job.pop("_id"))
        job_list.append(JobPosting(**job))

    return job_list


async def get_all_active_jobs(limit: int = 50) -> List[JobPosting]:
   
    cursor = jobs_collection.find(
        {"is_active": True}
    ).sort("posted_date", -1).limit(limit)

    job_list = []

    async for job in cursor:
        job["id"] = str(job.pop("_id"))
        job_list.append(JobPosting(**job))

    return job_list


async def update_job_posting(job_id: str, recruiter_id: str, updates: dict) -> Optional[JobPosting]:
    try:
        object_id = ObjectId(job_id)
    except Exception:
        return None

    # Strip None values — only update fields explicitly provided
    update_data = {k: v for k, v in updates.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    result = await jobs_collection.update_one(
        {"_id": object_id, "recruiter_id": recruiter_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    updated = await jobs_collection.find_one({"_id": object_id})
    if updated:
        updated["id"] = str(updated.pop("_id"))
        return JobPosting(**updated)

    return None


async def deactivate_job(job_id: str, recruiter_id: str) -> bool:
   
    try:
        object_id = ObjectId(job_id)
    except Exception:
        return False

    result = await jobs_collection.update_one(
        {
            "_id": object_id,
            "recruiter_id": recruiter_id    # ownership check
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return result.modified_count == 1
