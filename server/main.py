from fastapi import FastAPI

from app.db.database import Base
from app.db.database import engine

from app.models.user import User 

from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="AI Interview Copilot",
    version="1.0.0"
)

app.include_router(auth_router)

@app.get("/")
def root():
    return {"message" : "AI Interview Copilot API"}