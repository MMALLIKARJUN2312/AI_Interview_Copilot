from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models

from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router
from app.api.v1.interview import router as interview_router
from app.core.config import settings

app = FastAPI(
    title="AI Interview Copilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(interview_router)

@app.get("/")
def root():
    return {"message" : "AI Interview Copilot API"}