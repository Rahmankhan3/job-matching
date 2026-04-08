import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.database import client, create_indexes
from app.routes.auth import router as auth_router
from app.routes.candidate import router as candidate_router
from app.routes.recruiter import router as recruiter_router
from app.routes.jobs import router as jobs_router
from app.routes.applications import router as applications_router
from app.routes.upload import router as upload_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command('ping')
        print(f"--------Database connected: {settings.DATABASE_NAME}-------------")
        await create_indexes()
        print("--------Indexes created successfully--------")
    except Exception as e:
        print(f"----------Database connection failed: {e}")
        raise
    
    yield
    
    client.close()
    print("-------Database connection closed--------")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(candidate_router)
app.include_router(recruiter_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(upload_router)

# Serve uploaded files as static assets
_uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

@app.get("/")
async def root():
    return {"message": "Job Tracker API is running!", "app_name": settings.APP_NAME}
