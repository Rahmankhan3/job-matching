from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    applied = "applied"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


class ApplicationBase(BaseModel):
    job_posting_id: str
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass



class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus        
    notes: Optional[str] = None



class Application(ApplicationBase):
    id: str
    candidate_id: str
    status: ApplicationStatus       
    applied_date: datetime
    notes: Optional[str] = None        # recruiter's private notes
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
