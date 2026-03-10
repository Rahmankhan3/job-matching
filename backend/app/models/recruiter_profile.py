from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RecruiterProfileCreate(BaseModel):
   
    company_name: str                     
    designation: Optional[str] = None           
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None


class RecruiterProfileUpdate(BaseModel):
 
    company_name: Optional[str] = None
    designation: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None


class RecruiterProfile(BaseModel):
    id: str                                       
    user_id: str                               
    company_name: str
    designation: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
