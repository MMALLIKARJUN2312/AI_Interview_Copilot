import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 registers every ORM model on Base.metadata
from app.ai.models import (
    AIGenerationResult,
    ResumeAnalysisResult,
    InterviewQuestionSetResult,
    InterviewQuestionItem,
    AnswerEvaluationResult,
    InterviewSummaryResult,
    LearningRoadmapResult,
    RoadmapItem,
    CodingQuestionSetResult,
    CodingQuestionItem,
    TestCaseItem,
)
from app.ai.orchestrator import AIOrchestrator
from app.db.database import Base
from app.db.session import get_db
from app.services.code_execution_service import CodeExecutionService, ExecutionOutcome
from app.services.resume_service import ResumeService
from main import app as fastapi_app

FAKE_RESUME_TEXT = "Experienced backend engineer skilled in Python, FastAPI, and PostgreSQL."

@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()

def _register_and_login(client : TestClient, email : str, password : str = "supersecret1") -> dict:
    client.post("/auth/register", json={"full_name": "Test User", "email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def auth_headers(client):
    return _register_and_login(client, "user@example.com")

@pytest.fixture()
def other_auth_headers(client):
    return _register_and_login(client, "other@example.com")

@pytest.fixture()
def fake_ai(monkeypatch):
    """Replaces every AIOrchestrator call with a deterministic canned response,
    and bypasses real PDF text extraction, so tests never hit a live LLM provider.
    """

    def fake_analyze_resume(self, resume_text, target_role, job_description=None):
        return AIGenerationResult(
            data=ResumeAnalysisResult(
                ats_score=82, strengths=["Strong Python"], weaknesses=["No K8s"], suggestions=["Add metrics"]
            ),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_generate_questions(self, resume_text, target_role, num_questions, job_description=None):
        questions = [
            InterviewQuestionItem(
                question=f"{target_role} question {i + 1}", category="technical", difficulty="medium"
            )
            for i in range(num_questions)
        ]
        return AIGenerationResult(
            data=InterviewQuestionSetResult(questions=questions),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_evaluate_answer(self, target_role, question, category, difficulty, answer):
        return AIGenerationResult(
            data=AnswerEvaluationResult(
                score=70, feedback="Reasonable answer.", strengths=["clarity"], improvements=["depth"]
            ),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_summarize_interview(self, target_role, transcript):
        return AIGenerationResult(
            data=InterviewSummaryResult(
                overall_score=72, summary="Decent performance.",
                strengths=["communication"], weaknesses=["system design depth"], recommendation="Lean hire",
            ),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_generate_roadmap(self, target_role, weaknesses, summary):
        return AIGenerationResult(
            data=LearningRoadmapResult(
                items=[RoadmapItem(topic="System Design", description="Study distributed systems", priority="high", resources=["DDIA book"])]
            ),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_generate_dsa_questions(self, resume_text, target_role, num_questions, job_description=None):
        questions = [
            CodingQuestionItem(
                question=f"{target_role} DSA problem {i + 1}: sum two integers read from stdin.",
                difficulty="medium",
                examples="Input: 2 3\nOutput: 5",
                constraints="-1000 <= a, b <= 1000",
                test_cases=[
                    TestCaseItem(input="2 3", expected_output="5", hidden=False),
                    TestCaseItem(input="10 20", expected_output="30", hidden=True),
                ],
            )
            for i in range(num_questions)
        ]
        return AIGenerationResult(
            data=CodingQuestionSetResult(questions=questions),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_generate_machine_coding_questions(self, resume_text, target_role, num_questions, job_description=None):
        questions = [
            CodingQuestionItem(
                question=f"{target_role} machine coding task {i + 1}: implement an in-memory rate limiter.",
                difficulty="medium",
                examples="",
                constraints="Support a fixed window rate limit per key.",
                test_cases=[],
            )
            for i in range(num_questions)
        ]
        return AIGenerationResult(
            data=CodingQuestionSetResult(questions=questions),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    def fake_evaluate_code(self, target_role, round_type, question, language, code, test_summary=None):
        return AIGenerationResult(
            data=AnswerEvaluationResult(
                score=75, feedback="Solid solution with clear structure.",
                strengths=["correct approach"], improvements=["add more comments"],
            ),
            provider="fake", model="fake-model", processing_time_ms=1,
        )

    monkeypatch.setattr(AIOrchestrator, "analyze_resume", fake_analyze_resume)
    monkeypatch.setattr(AIOrchestrator, "generate_interview_questions", fake_generate_questions)
    monkeypatch.setattr(AIOrchestrator, "evaluate_answer", fake_evaluate_answer)
    monkeypatch.setattr(AIOrchestrator, "summarize_interview", fake_summarize_interview)
    monkeypatch.setattr(AIOrchestrator, "generate_roadmap", fake_generate_roadmap)
    monkeypatch.setattr(AIOrchestrator, "generate_dsa_questions", fake_generate_dsa_questions)
    monkeypatch.setattr(AIOrchestrator, "generate_machine_coding_questions", fake_generate_machine_coding_questions)
    monkeypatch.setattr(AIOrchestrator, "evaluate_code", fake_evaluate_code)
    monkeypatch.setattr(ResumeService, "extract_text", staticmethod(lambda file_path: FAKE_RESUME_TEXT))

@pytest.fixture()
def fake_code_execution(monkeypatch):
    """Replaces real code execution (which would otherwise call the Piston API)
    with a deterministic fake: code containing the string "correct" passes
    every test case it's run against, anything else fails all of them.
    """
    from app.services.code_execution_service import TestCaseResult

    def fake_run_test_cases(self, language, code, test_cases):
        passes = "correct" in code
        return [
            TestCaseResult(
                input=case["input"],
                expected_output=case["expected_output"],
                actual_output=case["expected_output"] if passes else "wrong output",
                passed=passes,
                stderr="" if passes else "assertion mismatch",
                hidden=case.get("hidden", False),
            )
            for case in test_cases
        ]

    def fake_run(self, language, code, stdin=""):
        return ExecutionOutcome(stdout="ok", stderr="", exit_code=0, timed_out=False)

    monkeypatch.setattr(CodeExecutionService, "run_test_cases", fake_run_test_cases)
    monkeypatch.setattr(CodeExecutionService, "run", fake_run)

@pytest.fixture()
def uploaded_resume(client, auth_headers, fake_ai):
    files = {"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"target_role": "Backend Engineer", "job_description": "Build scalable APIs"}
    response = client.post("/resume/analyze", headers=auth_headers, files=files, data=data)
    assert response.status_code == 200, response.text
    return response.json()
