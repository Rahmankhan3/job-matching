from app.database import candidate_profiles_collection, recruiter_profiles_collection
from app.models.candidate_profile import CandidateProfile
from app.models.recruiter_profile import RecruiterProfile
from typing import Optional
from bson import ObjectId
from datetime import datetime


# ─── Candidate Profile ───────────────────────────────────────────────────────

async def get_candidate_profile(user_id: str) -> Optional[CandidateProfile]:
    doc = await candidate_profiles_collection.find_one({"user_id": user_id})
    if doc:
        doc["id"] = str(doc.pop("_id"))
        return CandidateProfile(**doc)
    return None


async def upsert_candidate_profile(user_id: str, data: dict) -> CandidateProfile:
    """Create or update a candidate profile. Returns the final profile."""
    existing = await candidate_profiles_collection.find_one({"user_id": user_id})

    now = datetime.utcnow()
    # Strip None values so we don't overwrite existing fields with None
    update_fields = {k: v for k, v in data.items() if v is not None}
    update_fields["updated_at"] = now

    if existing:
        await candidate_profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )
    else:
        doc = {
            "user_id": user_id,
            **update_fields,
            "created_at": now,
        }
        await candidate_profiles_collection.insert_one(doc)

    updated = await candidate_profiles_collection.find_one({"user_id": user_id})
    updated["id"] = str(updated.pop("_id"))
    return CandidateProfile(**updated)


# ─── Recruiter Profile ────────────────────────────────────────────────────────

async def get_recruiter_profile(user_id: str) -> Optional[RecruiterProfile]:
    doc = await recruiter_profiles_collection.find_one({"user_id": user_id})
    if doc:
        doc["id"] = str(doc.pop("_id"))
        return RecruiterProfile(**doc)
    return None


async def upsert_recruiter_profile(user_id: str, data: dict) -> RecruiterProfile:
    """Create or update a recruiter profile. Returns the final profile."""
    existing = await recruiter_profiles_collection.find_one({"user_id": user_id})

    now = datetime.utcnow()
    update_fields = {k: v for k, v in data.items() if v is not None}
    update_fields["updated_at"] = now

    if existing:
        await recruiter_profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )
    else:
        doc = {
            "user_id": user_id,
            **update_fields,
            "created_at": now,
        }
        await recruiter_profiles_collection.insert_one(doc)

    updated = await recruiter_profiles_collection.find_one({"user_id": user_id})
    updated["id"] = str(updated.pop("_id"))
    return RecruiterProfile(**updated)
