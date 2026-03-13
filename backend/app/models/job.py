from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobPostingBase(BaseModel):
    title: str
    company: str
    location: str
    job_type: str  # "Full-time", "Intern", "Contract"
    description: str
    requirements: List[str]  
    salary_range: Optional[str] = None 
    deadline: Optional[datetime] = None


class JobPostingCreate(JobPostingBase):
    pass


class JobPosting(JobPostingBase):
    id: str
    recruiter_id: str
    is_active: bool = True
    posted_date: datetime
    created_at: datetime
    updated_at: datetime
        
    class Config:
        from_attributes = True
