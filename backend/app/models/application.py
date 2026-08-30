from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    applied = "applied"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


class StatusHistoryEvent(BaseModel):
    status: ApplicationStatus
    date: datetime
    notes: Optional[str] = None


class ApplicationBase(BaseModel):
    job_posting_id: str
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    form_responses: Optional[dict] = None       # custom recruiter-defined fields
    baseline_responses: Optional[dict] = None   # standard fields: mobile, gender, org, etc.


class ApplicationCreate(ApplicationBase):
    pass



class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus        
    notes: Optional[str] = None



class Application(ApplicationBase):
    id: str
    candidate_id: str
    status: ApplicationStatus       
    status_history: List[StatusHistoryEvent] = []
    applied_date: datetime
    notes: Optional[str] = None        # recruiter's private notes
    created_at: datetime
    updated_at: datetime

    # ── Phase 2: AI Ranking fields ────────────────────────────────────────
    parsed_resume_data: Optional[dict] = None
    match_scores: Optional[dict] = None
    final_match_score: Optional[float] = None
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    ranking_metadata: Optional[dict] = None
    ranking_status: Optional[str] = None
    eligibility_status: Optional[str] = None
    ranking_model_version: Optional[str] = None
    ranking_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
