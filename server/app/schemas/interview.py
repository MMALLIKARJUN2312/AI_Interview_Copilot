from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.constants import (
    VALID_ROUND_TYPES,
    MAX_QUESTIONS_PER_ROUND,
    DEFAULT_ROUND_COMPOSITION,
)

class RoundConfig(BaseModel):
    round_type : str
    num_questions : int = Field(ge=1, le=MAX_QUESTIONS_PER_ROUND)

    @model_validator(mode="after")
    def validate_round_type(self) -> "RoundConfig":
        if self.round_type not in VALID_ROUND_TYPES:
            raise ValueError(f"round_type must be one of {sorted(VALID_ROUND_TYPES)}")
        return self

class StartInterviewRequest(BaseModel):
    resume_id : int
    rounds : list[RoundConfig] = Field(
        default_factory=lambda: [RoundConfig(**item) for item in DEFAULT_ROUND_COMPOSITION],
    )

class TestCaseResponse(BaseModel):
    """A visible (non-hidden) test case shown to the candidate before they answer."""
    input : str
    expected_output : str

class ExecutionResultResponse(BaseModel):
    input : str
    expected_output : str
    actual_output : str
    passed : bool
    stderr : str

    model_config = {"from_attributes" : True}

class RunCodeRequest(BaseModel):
    question_id : int
    code : str = Field(min_length=1)
    language : str

class RunCodeResponse(BaseModel):
    results : list[ExecutionResultResponse]
    all_passed : bool

class AnswerResponse(BaseModel):
    id : int
    question_id : int
    score : int
    feedback : str
    strengths : list[str]
    improvements : list[str]
    language : str | None = None
    passed_test_count : int | None = None
    total_test_count : int | None = None
    execution_results : list[ExecutionResultResponse] | None = None

    model_config = {"from_attributes" : True}

class QuestionResponse(BaseModel):
    id : int
    order_index : int
    question_text : str
    category : str
    difficulty : str
    round_type : str
    language : str | None = None
    starter_code : str | None = None
    examples : str | None = None
    constraints : str | None = None
    test_cases : list[TestCaseResponse] = Field(default_factory=list)

    model_config = {"from_attributes" : True}

    @model_validator(mode="before")
    @classmethod
    def extract_round_type_and_visible_tests(cls, data):
        # Accept either an ORM InterviewQuestion instance or a plain dict. Runs
        # for QuestionWithAnswerResponse too (inherited), so it must also
        # carry the "answer" attribute through when present, converting it
        # explicitly rather than relying on from_attributes inference for a
        # value that's arriving inside an already-built dict.
        if hasattr(data, "round_type"):
            round_type = data.round_type
            round_type_value = round_type.value if hasattr(round_type, "value") else round_type
            all_cases = data.test_cases or []
            visible_cases = [case for case in all_cases if not case.get("hidden")]
            result = {
                "id": data.id,
                "order_index": data.order_index,
                "question_text": data.question_text,
                "category": data.category,
                "difficulty": data.difficulty,
                "round_type": round_type_value,
                "language": data.language,
                "starter_code": data.starter_code,
                "examples": data.examples,
                "constraints": data.constraints,
                "test_cases": [
                    {"input": case["input"], "expected_output": case["expected_output"]}
                    for case in visible_cases
                ],
            }
            if hasattr(data, "answer"):
                result["answer"] = AnswerResponse.model_validate(data.answer) if data.answer else None
            return result
        return data

class QuestionWithAnswerResponse(QuestionResponse):
    answer : AnswerResponse | None = None

class AnswerSubmitRequest(BaseModel):
    question_id : int
    answer_text : str | None = None
    code : str | None = None
    language : str | None = None

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
