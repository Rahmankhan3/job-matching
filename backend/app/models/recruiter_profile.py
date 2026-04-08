from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CompanyReview(BaseModel):
    author: str
    rating: float
    review_text: str
    date: datetime


class RecruiterProfileCreate(BaseModel):
   
    company_name: str                     
    designation: Optional[str] = None           
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    company_reviews: List[CompanyReview] = []


class RecruiterProfileUpdate(BaseModel):
 
    company_name: Optional[str] = None
    designation: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    company_reviews: Optional[List[CompanyReview]] = None


class RecruiterProfile(BaseModel):
    id: str
    user_id: str
    company_name: Optional[str] = None
    designation: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    company_reviews: List[CompanyReview] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
