from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    candidate = "candidate"
    recruiter = "recruiter"


class UserBase(BaseModel):
    email: EmailStr      
    role: UserRole     


class UserCreate(UserBase):
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    password_hash: str  
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
