from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ExperienceLevel(str, Enum):
    fresher = "fresher"         
    junior = "junior"           
    mid = "mid"                
    senior = "senior"


class CandidateProfileCreate(BaseModel):
    
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = []       
    experience_level: Optional[ExperienceLevel] = ExperienceLevel.fresher
    resume_url: Optional[str] = None      
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class CandidateProfileUpdate(BaseModel):
 
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_level: Optional[ExperienceLevel] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None



class CandidateProfile(BaseModel):
   
    id: str                                       
    user_id: str                         
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    experience_level: ExperienceLevel = ExperienceLevel.fresher
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
