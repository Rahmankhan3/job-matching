import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Annotated
from app.middleware.auth_middleware import get_current_candidate, get_current_recruiter
from app.models.user import User

# ── Directory setup ────────────────────────────────────────────────────────────
RESUME_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "resumes")
LOGO_DIR   = os.path.join(os.path.dirname(__file__), "..", "uploads", "logos")
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(LOGO_DIR,   exist_ok=True)

RESUME_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
LOGO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png":  ".png",
}

router = APIRouter(prefix="/upload", tags=["Upload"])


# ── Resume upload (candidates only) ───────────────────────────────────────────
@router.post("/resume")
async def upload_resume(
    current_user: Annotated[User, Depends(get_current_candidate)],
    file: UploadFile = File(...),
):
    if file.content_type not in RESUME_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are accepted.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 5 MB.")

    ext = RESUME_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    with open(os.path.join(RESUME_DIR, filename), "wb") as f:
        f.write(contents)

    return {"url": f"http://localhost:8000/uploads/resumes/{filename}", "filename": file.filename}


# ── Company logo upload (recruiters only) ─────────────────────────────────────
@router.post("/logo")
async def upload_logo(
    current_user: Annotated[User, Depends(get_current_recruiter)],
    file: UploadFile = File(...),
):
    if file.content_type not in LOGO_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are accepted.")

    contents = await file.read()
    if len(contents) > 1 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo must be under 1 MB.")

    ext = LOGO_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    with open(os.path.join(LOGO_DIR, filename), "wb") as f:
        f.write(contents)

    return {"url": f"http://localhost:8000/uploads/logos/{filename}", "filename": file.filename}
