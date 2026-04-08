from app.database import applications_collection, jobs_collection, users_collection
from app.models.application import Application, ApplicationStatus
from app.models.application_view import (
    ApplicationCandidateView,
    ApplicationRecruiterView,
    CandidateSummary,
    JobSummary
)
from typing import List, Optional
from bson import ObjectId
from datetime import datetime


async def create_application(
    candidate_id: str,
    job_posting_id: str,
    application_data: dict
) -> Optional[Application]:
   
    try:
        job_object_id = ObjectId(job_posting_id)
    except Exception:
        return None  # malformed job ID

    # Check job exists and is active
    job = await jobs_collection.find_one({
        "_id": job_object_id,
        "is_active": True
    })
    if not job:
        return None  # job not found or inactive

    # Check for duplicate application
    existing = await applications_collection.find_one({
        "candidate_id": candidate_id,
        "job_posting_id": job_posting_id
    })
    if existing:
        return None  # already applied

    # Validate resume — always required
    resume_url = application_data.get("resume_url")
    if not resume_url or not str(resume_url).strip():
        raise ValueError("CV / Resume is required to submit an application.")

    # Validate custom form fields
    form_fields = job.get("application_form_fields", []) or []
    form_responses = application_data.get("form_responses") or {}
    missing_labels = []
    for field in form_fields:
        if field.get("required"):
            value = form_responses.get(field["field_id"])
            if value is None or str(value).strip() == "":
                missing_labels.append(field["label"])
    if missing_labels:
        raise ValueError(f"Required fields missing: {', '.join(missing_labels)}")

    application_doc = {
        "candidate_id": candidate_id,
        "job_posting_id": job_posting_id,
        "cover_letter": application_data.get("cover_letter"),
        "resume_url": application_data.get("resume_url"),
        "form_responses": form_responses,
        "baseline_responses": application_data.get("baseline_responses") or {},
        "status": ApplicationStatus.applied.value,
        "status_history": [{
            "status": ApplicationStatus.applied.value,
            "date": datetime.utcnow(),
            "notes": None
        }],
        "applied_date": datetime.utcnow(),
        "notes": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await applications_collection.insert_one(application_doc)

    if result.inserted_id:
        created_app = await applications_collection.find_one(
            {"_id": result.inserted_id}
        )
        created_app["id"] = str(created_app.pop("_id"))
        return Application(**created_app)

    return None


async def get_application_by_id(application_id: str) -> Optional[Application]:

    try:
        object_id = ObjectId(application_id)
    except Exception:
        return None

    app_doc = await applications_collection.find_one({"_id": object_id})

    if app_doc:
        app_doc["id"] = str(app_doc.pop("_id"))
        return Application(**app_doc)

    return None


async def get_applications_by_candidate(
    candidate_id: str
) -> List[Application]:
  
    cursor = applications_collection.find(
        {"candidate_id": candidate_id}
    ).sort("applied_date", -1)

    app_list = []
    async for app in cursor:
        app["id"] = str(app.pop("_id"))
        app_list.append(Application(**app))

    return app_list


async def get_applications_by_candidate_with_job( # gives info of all applications along with job details like title, company, etc
    candidate_id: str
) -> List[ApplicationCandidateView]:

    cursor = applications_collection.find(
        {"candidate_id": candidate_id}
    ).sort("applied_date", -1)

    result = []

    async for app in cursor:
       
        try:
            job = await jobs_collection.find_one(
                {"_id": ObjectId(app["job_posting_id"])},
                {"title": 1, "company": 1} 
            )
        except Exception:
            continue 

        if not job:
            continue 

        job_summary = JobSummary(
            id=str(job["_id"]),
            title=job["title"],
            company=job["company"]
        )

        result.append(ApplicationCandidateView(
            id=str(app["_id"]),
            job=job_summary,
            status=app["status"],
            status_history=app.get("status_history", []),
            applied_date=app["applied_date"],
            notes=app.get("notes"),
            form_responses=app.get("form_responses"),
            baseline_responses=app.get("baseline_responses"),
        ))

    return result


async def get_applications_by_job( # gives info of all applications along with candidate details like email, role, etc
    job_posting_id: str
) -> List[ApplicationRecruiterView]:

    cursor = applications_collection.find(
        {"job_posting_id": job_posting_id}
    ).sort("applied_date", -1)
    app_list = []

    async for app in cursor:
        app_data = dict(app)
        app_data["id"] = str(app_data.pop("_id"))

        candidate_summary = None
        try:
            candidate = await users_collection.find_one(
                {"_id": ObjectId(app_data["candidate_id"])},
                {"email": 1, "role": 1}  
            )
            if candidate:
                candidate_summary = CandidateSummary(
                    id=str(candidate["_id"]),
                    email=candidate["email"],
                    role=candidate["role"]
                )
        except Exception:
         
            candidate_summary = None

        app_data["candidate"] = candidate_summary
        app_list.append(ApplicationRecruiterView(**app_data))

    return app_list


async def update_application_status(
    application_id: str,
    recruiter_id: str,
    new_status: str,
    notes: Optional[str] = None
) -> Optional[Application]:
  
    try:
        app_object_id = ObjectId(application_id)
    except Exception:
        return None

    # Step 1 — find the application
    app = await applications_collection.find_one({"_id": app_object_id})
    if not app:
        return None

    # Step 2 — verify recruiter owns the job this application belongs to
    try:
        job = await jobs_collection.find_one({
            "_id": ObjectId(app["job_posting_id"]),
            "recruiter_id": recruiter_id        # ownership check
        })
    except Exception:
        return None

    if not job:
        return None  # recruiter doesn't own this job — access denied

    # Step 3 — perform the update
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }

    # Only add notes to update if provided — don't overwrite existing notes with None
    if notes is not None:
        update_data["notes"] = notes

    result = await applications_collection.update_one(
        {"_id": app_object_id},
        {
            "$set": update_data,
            "$push": {
                "status_history": {
                    "status": new_status,
                    "date": datetime.utcnow(),
                    "notes": notes
                }
            }
        }
    )

    if result.modified_count > 0:
        updated_app = await applications_collection.find_one(
            {"_id": app_object_id}
        )
        updated_app["id"] = str(updated_app.pop("_id"))
        return Application(**updated_app)

    return None
