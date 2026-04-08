from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobSectionsVisibility(BaseModel):
    show_requirements: bool = True
    show_qualifications: bool = True
    show_salary: bool = True
    show_additional_info: bool = True
    show_company_logo: bool = True


class FAQ(BaseModel):
    question: str
    answer: str


class ApplicationFormField(BaseModel):
    field_id: str
    label: str
    field_type: str   # text | textarea | number | url | select | checkbox
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None


class JobPostingBase(BaseModel):

    # ── 1. Job Details 
    title: str = Field(..., max_length=190)
    company: str
    company_logo: Optional[str] = None
    work_arrangement: Optional[str] = None     # Full Time | Part Time | Contractual
    num_openings: Optional[int] = None
    hide_openings: bool = False
    link_festival: Optional[str] = None
    registration_start: Optional[datetime] = None
    deadline: Optional[datetime] = None

    # ── 2. Work Location 
    work_setup: Optional[str] = None           # In Office | Work from Home | Hybrid | Field Job
    work_location: Optional[str] = None

    # ── 3. Application Criteria 
    candidate_type: List[str] = []  # Clg students | Freshers | Everyone | Professionals
    passing_year: List[str] = []
    educational_background: List[str] = [] 
    college_restrictor: Optional[str] = None
    gender_restrictor: Optional[str] = None

    # ── 4. About the Role & Skills 
    roles: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: List[str] = []
    qualifications: Optional[List[str]] = None
    skills_required: List[str] = []
    additional_information: Optional[str] = None
    faqs: Optional[List[FAQ]] = None

    # ── 5. Salary & Benefits 
    pay_structure: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    hide_salary: bool = False
    benefits: List[str] = []

    # ── Visibility & Form 
    visibility: JobSectionsVisibility = Field(default_factory=JobSectionsVisibility)
    application_form_fields: List[ApplicationFormField] = Field(default_factory=list)


class JobPostingCreate(JobPostingBase):
    pass


class JobPostingUpdate(BaseModel):
    """All fields optional for PATCH updates."""
    title: Optional[str] = Field(default=None, max_length=190)
    company: Optional[str] = None
    company_logo: Optional[str] = None
    work_arrangement: Optional[str] = None
    num_openings: Optional[int] = None
    hide_openings: Optional[bool] = None
    link_festival: Optional[str] = None
    registration_start: Optional[datetime] = None
    deadline: Optional[datetime] = None
    work_setup: Optional[str] = None
    work_location: Optional[str] = None
    candidate_type: Optional[List[str]] = None
    passing_year: Optional[List[str]] = None
    educational_background: Optional[List[str]] = None
    college_restrictor: Optional[str] = None
    gender_restrictor: Optional[str] = None
    roles: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    additional_information: Optional[str] = None
    faqs: Optional[List[FAQ]] = None
    pay_structure: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    hide_salary: Optional[bool] = None
    benefits: Optional[List[str]] = None
    visibility: Optional[JobSectionsVisibility] = None
    application_form_fields: Optional[List[ApplicationFormField]] = None



class JobPosting(JobPostingBase):
    id: str
    recruiter_id: str
    is_active: bool = True
    posted_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
