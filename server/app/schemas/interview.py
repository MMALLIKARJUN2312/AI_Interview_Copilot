from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import (
    DEFAULT_INTERVIEW_QUESTION_COUNT,
    MIN_INTERVIEW_QUESTIONS,
    MAX_INTERVIEW_QUESTIONS,
)

class StartInterviewRequest(BaseModel):
    resume_id : int
    num_questions : int = Field(
        default=DEFAULT_INTERVIEW_QUESTION_COUNT,
        ge=MIN_INTERVIEW_QUESTIONS,
        le=MAX_INTERVIEW_QUESTIONS,
    )

class AnswerResponse(BaseModel):
    id : int
    question_id : int
    score : int
    feedback : str
    strengths : list[str]
    improvements : list[str]

    model_config = {"from_attributes" : True}

class QuestionResponse(BaseModel):
    id : int
    order_index : int
    question_text : str
    category : str
    difficulty : str

    model_config = {"from_attributes" : True}

class QuestionWithAnswerResponse(QuestionResponse):
    answer : AnswerResponse | None = None

class AnswerSubmitRequest(BaseModel):
    question_id : int
    answer_text : str = Field(min_length=1)

class SessionSummary(BaseModel):
    id : int
    resume_id : int
    target_role : str
    status : str
    total_questions : int
    current_index : int
    overall_score : int | None
    created_at : datetime
    completed_at : datetime | None

    model_config = {"from_attributes" : True}

class StartInterviewResponse(BaseModel):
    session : SessionSummary
    first_question : QuestionResponse | None

class SubmitAnswerResponse(BaseModel):
    answer : AnswerResponse
    next_question : QuestionResponse | None
    is_complete : bool

class FeedbackResponse(BaseModel):
    overall_score : int
    summary : str
    strengths : list[str]
    weaknesses : list[str]
    recommendation : str

    model_config = {"from_attributes" : True}

class RoadmapItemResponse(BaseModel):
    topic : str
    description : str
    priority : str
    resources : list[str]

class RoadmapResponse(BaseModel):
    items : list[RoadmapItemResponse]

class CompleteInterviewResponse(BaseModel):
    session : SessionSummary
    feedback : FeedbackResponse
    roadmap : RoadmapResponse

class SessionDetailResponse(BaseModel):
    session : SessionSummary
    questions : list[QuestionWithAnswerResponse]
    feedback : FeedbackResponse | None
    roadmap : RoadmapResponse | None
