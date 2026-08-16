from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

@dataclass
class AIGenerationResult(Generic[T]):
    """Wraps a validated AI response together with generation metadata
    needed for persistence and observability (provider, model, latency).
    """

    data : T
    provider : str
    model : str
    processing_time_ms : int

class ResumeAnalysisResult(BaseModel):
    """Standardized AI response for resume analysis"""
    
    ats_score : int = Field(
        ge=0,
        le=100,
        description="ATS score between 0 and 100"
    )
    strengths : list[str]
    weaknesses : list[str]
    suggestions : list[str]

class InterviewQuestionItem(BaseModel):
    """A single AI-generated interview question"""

    question : str
    category : str = Field(description="e.g. technical, behavioral, system_design")
    difficulty : str = Field(description="easy, medium, or hard")

class InterviewQuestionSetResult(BaseModel):
    """Standardized AI response for role-aligned interview question generation"""

    questions : list[InterviewQuestionItem]

class TestCaseItem(BaseModel):
    """A single input/output test case for a coding question"""

    input : str
    expected_output : str
    hidden : bool = Field(
        default=False,
        description="Hidden test cases are used for scoring but never shown to the candidate",
    )

class CodingQuestionItem(BaseModel):
    """A single AI-generated coding question (DSA or machine coding)"""

    question : str = Field(description="The full problem statement")
    difficulty : str = Field(description="easy, medium, or hard")
    examples : str = Field(default="", description="Human-readable worked examples")
    constraints : str = Field(default="", description="Input size / edge-case constraints, if any")
    test_cases : list[TestCaseItem] = Field(
        default_factory=list,
        description="Input/output test cases; empty for open-ended machine-coding tasks",
    )

class CodingQuestionSetResult(BaseModel):
    """Standardized AI response for coding question generation"""

    questions : list[CodingQuestionItem]

class AnswerEvaluationResult(BaseModel):
    """Standardized AI response for evaluating a single interview answer"""

    score : int = Field(ge=0, le=100, description="Answer quality score between 0 and 100")
    feedback : str
    strengths : list[str]
    improvements : list[str]

class InterviewSummaryResult(BaseModel):
    """Standardized AI response for the end-of-session interview summary"""

    overall_score : int = Field(ge=0, le=100)
    summary : str
    strengths : list[str]
    weaknesses : list[str]
    recommendation : str

class RoadmapItem(BaseModel):
    """A single learning roadmap topic"""

    topic : str
    description : str
    priority : str = Field(description="high, medium, or low")
    resources : list[str]

class LearningRoadmapResult(BaseModel):
    """Standardized AI response for a personalized learning roadmap"""

    items : list[RoadmapItem]