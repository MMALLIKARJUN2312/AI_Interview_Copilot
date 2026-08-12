import uuid

from fastapi import (APIRouter, UploadFile, File, Form, Depends, HTTPException, Request)
from sqlalchemy.orm import Session

from app.services.resume_service import ResumeService
from app.services.storage import get_storage_backend
from app.core.constants import (MAX_RESUME_SIZE, ALLOWED_RESUME_TYPES, PDF_MAGIC_BYTES)
from app.core.logger import logger
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.models.resume import Resume, ResumeStatus
from app.models.resume_analysis import ResumeAnalysis, AnalysisStatus
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.schemas.resume import ResumeSummary
from app.schemas.resume_analysis import ResumeAnalysisResponse

router = APIRouter(
    prefix='/resume',
    tags=["Resume"]
)

resume_repository = ResumeRepository()
resume_analysis_repository = ResumeAnalysisRepository()

@router.post('/analyze', response_model=ResumeAnalysisResponse)
@limiter.limit("10/hour")
async def analyze_resume(
    request : Request,
    file : UploadFile = File(...),
    target_role : str = Form(..., min_length=2, max_length=150),
    job_description : str | None = Form(None),
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    try :
        logger.info(
            "Resume upload received: %s (role=%s, user_id=%s)",
            file.filename, target_role, current_user.id
        )

        if (file.content_type not in ALLOWED_RESUME_TYPES):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        contents = await file.read()

        max_size = (MAX_RESUME_SIZE * 1024 * 1024)

        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail=f"File exceeds {MAX_RESUME_SIZE} MB")

        if not contents.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(status_code=400, detail="File does not look like a valid PDF")

        storage = get_storage_backend()
        stored_filename = f"{uuid.uuid4()}.pdf"
        await storage.save(stored_filename, contents)

        resume = Resume(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            mime_type=file.content_type,
            file_size=len(contents),
            target_role=target_role,
            job_description=job_description,
            status=ResumeStatus.UPLOADED,
        )
        resume_repository.create_resume(db, resume)
        resume_repository.commit(db)
        resume_repository.refresh(db, resume)

        resume_service = ResumeService()

        try:
            extracted_text = resume_service.extract_text(contents)
            generation = resume_service.analyze_resume(extracted_text, target_role, job_description)
        except Exception as ai_error:
            resume_repository.mark_failed(resume)
            resume_analysis_repository.create_analysis(db, ResumeAnalysis(
                resume_id=resume.id,
                ats_score=0,
                strengths=[],
                weaknesses=[],
                suggestions=[],
                provider="unknown",
                model="unknown",
                processing_time_ms=0,
                status=AnalysisStatus.FAILED,
                error_message=str(ai_error)[:500],
            ))
            resume_repository.commit(db)
            raise

        result = generation.data

        resume.extracted_text = extracted_text

        analysis = ResumeAnalysis(
            resume_id=resume.id,
            ats_score=result.ats_score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestions=result.suggestions,
            provider=generation.provider,
            model=generation.model,
            processing_time_ms=generation.processing_time_ms,
            status=AnalysisStatus.SUCCESS,
        )
        resume_analysis_repository.create_analysis(db, analysis)
        resume_repository.mark_analyzed(resume)
        resume_repository.commit(db)
        resume_repository.refresh(db, analysis)

        return ResumeAnalysisResponse(
            resume_id=resume.id,
            analysis_id=analysis.id,
            target_role=resume.target_role,
            ats_score=result.ats_score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestions=result.suggestions,
        )

    except HTTPException:
        raise
    except ValueError as error :
        raise HTTPException(status_code=400, detail=str(error))
    except Exception :
        logger.exception("Resume analysis failed")
        raise HTTPException(status_code=500, detail=("Resume analysis failed"))

@router.get('/', response_model=list[ResumeSummary])
def list_resumes(
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    return resume_repository.get_user_resumes(db, current_user.id)

@router.get('/{resume_id}', response_model=ResumeSummary)
def get_resume(
    resume_id : int,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    resume = resume_repository.get_by_id(db, resume_id)

    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    return resume

@router.get('/{resume_id}/analysis', response_model=ResumeAnalysisResponse)
def get_resume_analysis(
    resume_id : int,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    resume = resume_repository.get_by_id(db, resume_id)

    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    analysis = resume_analysis_repository.get_latest_analysis(db, resume.id)

    if analysis is None or analysis.status != AnalysisStatus.SUCCESS:
        raise HTTPException(status_code=404, detail="No successful analysis found for this resume")

    return ResumeAnalysisResponse(
        resume_id=resume.id,
        analysis_id=analysis.id,
        target_role=resume.target_role,
        ats_score=analysis.ats_score,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        suggestions=analysis.suggestions,
    )
