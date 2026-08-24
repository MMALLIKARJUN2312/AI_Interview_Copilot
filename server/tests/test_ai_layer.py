import pytest
from pydantic import BaseModel

from app.ai.exceptions import AIResponseParsingError, AIResponseValidationError
from app.ai.parser import AIResponseParser
from app.ai.prompts.interview import InterviewQuestionGenerationPrompt, AnswerEvaluationPrompt
from app.ai.prompts.resume import ResumeAnalysisPrompt
from app.ai.validator import AIResponseValidator

def test_resume_analysis_prompt_includes_target_role():
    prompt = ResumeAnalysisPrompt().build(resume_text="John Doe resume", target_role="Backend Engineer")

    assert "Backend Engineer" in prompt
    assert "John Doe resume" in prompt

def test_resume_analysis_prompt_includes_job_description_when_given():
    prompt = ResumeAnalysisPrompt().build(
        resume_text="resume", target_role="Backend Engineer", job_description="Own the payments API"
    )

    assert "Own the payments API" in prompt

def test_interview_question_prompt_is_role_specific():
    prompt = InterviewQuestionGenerationPrompt().build(
        resume_text="resume text", target_role="Data Scientist", num_questions=5
    )

    assert "Data Scientist" in prompt
    assert "5" in prompt

def test_answer_evaluation_prompt_includes_question_and_answer():
    prompt = AnswerEvaluationPrompt().build(
        target_role="Backend Engineer", question="Explain indexing", category="technical",
        difficulty="medium", answer="An index speeds up lookups",
    )

    assert "Explain indexing" in prompt
    assert "An index speeds up lookups" in prompt

def test_parser_strips_markdown_fences():
    raw = '```json\n{"a": 1}\n```'

    assert AIResponseParser.parse_json(raw) == {"a": 1}

def test_parser_raises_on_empty_response():
    with pytest.raises(AIResponseParsingError):
        AIResponseParser.parse_json("")

def test_parser_raises_on_invalid_json():
    with pytest.raises(AIResponseParsingError):
        AIResponseParser.parse_json("not json at all")

class _Sample(BaseModel):
    score : int

def test_validator_accepts_matching_schema():
    result = AIResponseValidator.validate(response={"score": 10}, response_model=_Sample)

    assert result.score == 10

def test_validator_raises_on_schema_mismatch():
    with pytest.raises(AIResponseValidationError):
        AIResponseValidator.validate(response={"score": "not-a-number"}, response_model=_Sample)

def test_parser_raises_on_invalid_escape():
    raw = r'''
    {
        "solution": "Use \d+ to match digits"
    }
    '''

    with pytest.raises(AIResponseParsingError):
        AIResponseParser.parse_json(raw)

def test_parser_accepts_escaped_backslash():
    raw = r'''
    {
        "solution": "Use \\d+ to match digits"
    }
    '''

    result = AIResponseParser.parse_json(raw)

    assert result["solution"] == r"Use \d+ to match digits"
