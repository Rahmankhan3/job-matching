from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.application import StatusHistoryEvent
from datetime import datetime

class JobSummary(BaseModel):
    id: str
    title: str
    company: str


class ApplicationCandidateView(BaseModel):
    id: str
    job: JobSummary
    status: str
    status_history: List[StatusHistoryEvent] = []
    applied_date: datetime
    notes: Optional[str] = None
    form_responses: Optional[dict] = None
    baseline_responses: Optional[dict] = None

    class Config:
        from_attributes = True


class CandidateSummary(BaseModel):
    """Safe candidate info for recruiters."""
    id: str
    email: str
    role: str


class ApplicationRecruiterView(BaseModel):
    """Full application view for recruiters with candidate details."""
    id: str
    job_posting_id: str
    candidate: Optional[CandidateSummary] = Field(default=None)
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    form_responses: Optional[dict] = None
    baseline_responses: Optional[dict] = None
    status: str
    status_history: List[StatusHistoryEvent] = []
    applied_date: datetime
    notes: Optional[str] = None
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
