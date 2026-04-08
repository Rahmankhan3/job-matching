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

    class Config:
        from_attributes = True
