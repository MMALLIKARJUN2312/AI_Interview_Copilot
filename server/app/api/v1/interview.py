from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.logger import logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.interview_repository import InterviewSessionRepository
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.interview_feedback_repository import InterviewFeedbackRepository
from app.repositories.learning_roadmap_repository import LearningRoadmapRepository
from app.schemas.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    AnswerSubmitRequest,
    SubmitAnswerResponse,
    CompleteInterviewResponse,
    SessionDetailResponse,
    SessionSummary,
    QuestionResponse,
    QuestionWithAnswerResponse,
    AnswerResponse,
    FeedbackResponse,
    RoadmapResponse,
)
from app.services.interview_service import InterviewService

router = APIRouter(
    prefix='/interview',
    tags=["Interview"]
)

interview_service = InterviewService()
session_repository = InterviewSessionRepository()
question_repository = InterviewQuestionRepository()
feedback_repository = InterviewFeedbackRepository()
roadmap_repository = LearningRoadmapRepository()

@router.post('/start', response_model=StartInterviewResponse)
def start_interview(
    payload : StartInterviewRequest,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    try:
        logger.info(
            "Starting interview session: resume_id=%s, user_id=%s",
            payload.resume_id, current_user.id
        )
        session = interview_service.start_session(
            db, current_user.id, payload.resume_id, payload.num_questions
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        logger.exception("Failed to start interview session")
        raise HTTPException(status_code=500, detail="Failed to start interview session")

    first_question = interview_service.get_next_question(db, current_user.id, session.id)

    return StartInterviewResponse(
        session=SessionSummary.model_validate(session),
        first_question=QuestionResponse.model_validate(first_question) if first_question else None,
    )

@router.post('/{session_id}/answer', response_model=SubmitAnswerResponse)
def submit_answer(
    session_id : int,
    payload : AnswerSubmitRequest,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    try:
        answer = interview_service.submit_answer(
            db, current_user.id, session_id, payload.question_id, payload.answer_text
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        logger.exception("Failed to submit interview answer")
        raise HTTPException(status_code=500, detail="Failed to submit interview answer")

    next_question = interview_service.get_next_question(db, current_user.id, session_id)

    return SubmitAnswerResponse(
        answer=AnswerResponse.model_validate(answer),
        next_question=QuestionResponse.model_validate(next_question) if next_question else None,
        is_complete=next_question is None,
    )

@router.post('/{session_id}/complete', response_model=CompleteInterviewResponse)
def complete_interview(
    session_id : int,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    try:
        session = interview_service.complete_session(db, current_user.id, session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        logger.exception("Failed to complete interview session")
        raise HTTPException(status_code=500, detail="Failed to complete interview session")

    feedback = feedback_repository.get_by_session(db, session.id)
    roadmap = roadmap_repository.get_by_session(db, session.id)

    return CompleteInterviewResponse(
        session=SessionSummary.model_validate(session),
        feedback=FeedbackResponse.model_validate(feedback),
        roadmap=RoadmapResponse(items=roadmap.items),
    )

@router.get('/sessions', response_model=list[SessionSummary])
def list_sessions(
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    sessions = session_repository.get_user_sessions(db, current_user.id)
    return [SessionSummary.model_validate(session) for session in sessions]

@router.get('/{session_id}', response_model=SessionDetailResponse)
def get_session_detail(
    session_id : int,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    session = session_repository.get_by_id(db, session_id)

    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Interview session not found")

    questions = question_repository.get_by_session(db, session.id)
    feedback = feedback_repository.get_by_session(db, session.id)
    roadmap = roadmap_repository.get_by_session(db, session.id)

    return SessionDetailResponse(
        session=SessionSummary.model_validate(session),
        questions=[QuestionWithAnswerResponse.model_validate(question) for question in questions],
        feedback=FeedbackResponse.model_validate(feedback) if feedback else None,
        roadmap=RoadmapResponse(items=roadmap.items) if roadmap else None,
    )
