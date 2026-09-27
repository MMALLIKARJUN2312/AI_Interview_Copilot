import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import app.models

from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router
from app.api.v1.interview import router as interview_router
from app.core.config import settings
from app.core.logger import logger
from app.core.rate_limit import limiter
from app.db.session import get_db

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

app = FastAPI(
    title="AI Interview Copilot",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request : Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "%s %s -> %s (%sms)",
        request.method, request.url.path, response.status_code, duration_ms
    )

    return response

@app.exception_handler(Exception)
async def unhandled_exception_handler(request : Request, exc : Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)

    return JSONResponse(status_code=500, content={"detail" : "Internal server error"})

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(interview_router)

@app.get("/")
def root():
    return {"message" : "AI Interview Copilot API"}

@app.get("/health")
def health():
    return {"status" : "ok"}

@app.get("/health/ready")
def readiness_check(
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.warning(
            "Database readiness check failed: %s",
            error,
        )
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from error

    return {"status": "ready"}
