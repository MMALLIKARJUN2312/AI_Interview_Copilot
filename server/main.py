from fastapi import FastAPI

import app.models

from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router

app = FastAPI(
    title="AI Interview Copilot",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(resume_router)   

@app.get("/")
def root():
    return {"message" : "AI Interview Copilot API"}