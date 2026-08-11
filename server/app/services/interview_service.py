from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.orchestrator import AIOrchestrator
from app.core.constants import (
    VALID_QUESTION_CATEGORIES,
    VALID_QUESTION_DIFFICULTIES,
    DEFAULT_QUESTION_CATEGORY,
    DEFAULT_QUESTION_DIFFICULTY,
)
from app.models.interview import (
    InterviewSession,
    InterviewSessionStatus,
    InterviewQuestion,
    InterviewAnswer,
    InterviewFeedback,
    LearningRoadmap,
)
from app.repositories.interview_repository import InterviewSessionRepository
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.interview_answer_repository import InterviewAnswerRepository
from app.repositories.interview_feedback_repository import InterviewFeedbackRepository
from app.repositories.learning_roadmap_repository import LearningRoadmapRepository
from app.repositories.resume_repository import ResumeRepository

def _normalize(value : str, valid_values : set[str], default : str) -> str:
    normalized = (value or "").strip().lower().replace(" ", "_")
    return normalized if normalized in valid_values else default

class InterviewService:
    """Orchestrates the full lifecycle of a role-aligned mock interview session:
    generating questions from a resume, evaluating answers, and producing
    end-of-session feedback and a learning roadmap.
    """

    def __init__(self) -> None:
        self.ai = AIOrchestrator()
        self.session_repo = InterviewSessionRepository()
        self.question_repo = InterviewQuestionRepository()
        self.answer_repo = InterviewAnswerRepository()
        self.feedback_repo = InterviewFeedbackRepository()
        self.roadmap_repo = LearningRoadmapRepository()
        self.resume_repo = ResumeRepository()

    def _get_owned_session(self, db : Session, user_id : int, session_id : int) -> InterviewSession:
        session = self.session_repo.get_by_id(db, session_id)

        if session is None or session.user_id != user_id:
            raise ValueError("Interview session not found")

        return session

    def start_session(
        self,
        db : Session,
        user_id : int,
        resume_id : int,
        num_questions : int,
    ) -> InterviewSession:
        resume = self.resume_repo.get_by_id(db, resume_id)

        if resume is None or resume.user_id != user_id:
            raise ValueError("Resume not found")

        if not resume.extracted_text:
            raise ValueError("This resume has no extracted text yet; re-upload and analyze it first")

        generation = self.ai.generate_interview_questions(
            resume_text=resume.extracted_text,
            target_role=resume.target_role,
            num_questions=num_questions,
            job_description=resume.job_description,
        )
        generated_questions = generation.data.questions

        if not generated_questions:
            raise ValueError("The AI provider did not return any interview questions")

        session = InterviewSession(
            user_id=user_id,
            resume_id=resume.id,
            target_role=resume.target_role,
            status=InterviewSessionStatus.IN_PROGRESS,
            total_questions=len(generated_questions),
            current_index=0,
            provider=generation.provider,
            model=generation.model,
        )
        self.session_repo.create_session(db, session)
        self.session_repo.flush(db)

        questions = [
            InterviewQuestion(
                session_id=session.id,
                order_index=index,
                question_text=item.question,
                category=_normalize(item.category, VALID_QUESTION_CATEGORIES, DEFAULT_QUESTION_CATEGORY),
                difficulty=_normalize(item.difficulty, VALID_QUESTION_DIFFICULTIES, DEFAULT_QUESTION_DIFFICULTY),
            )
            for index, item in enumerate(generated_questions)
        ]
        self.question_repo.create_questions(db, questions)

        self.session_repo.commit(db)
        self.session_repo.refresh(db, session)

        return session

    def get_next_question(self, db : Session, user_id : int, session_id : int) -> InterviewQuestion | None:
        session = self._get_owned_session(db, user_id, session_id)

        return self.question_repo.get_next_unanswered(db, session.id)

    def submit_answer(
        self,
        db : Session,
        user_id : int,
        session_id : int,
        question_id : int,
        answer_text : str,
    ) -> InterviewAnswer:
        session = self._get_owned_session(db, user_id, session_id)

        if session.status != InterviewSessionStatus.IN_PROGRESS:
            raise ValueError("This interview session is not in progress")

        question = self.question_repo.get_by_id(db, question_id)

        if question is None or question.session_id != session.id:
            raise ValueError("Question not found in this session")

        if self.answer_repo.get_by_question(db, question.id) is not None:
            raise ValueError("This question has already been answered")

        generation = self.ai.evaluate_answer(
            target_role=session.target_role,
            question=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
            answer=answer_text,
        )
        result = generation.data

        answer = InterviewAnswer(
            question_id=question.id,
            answer_text=answer_text,
            score=result.score,
            feedback=result.feedback,
            strengths=result.strengths,
            improvements=result.improvements,
        )
        self.answer_repo.create_answer(db, answer)

        session.current_index += 1

        self.session_repo.commit(db)
        self.session_repo.refresh(db, answer)

        return answer

    def complete_session(self, db : Session, user_id : int, session_id : int) -> InterviewSession:
        session = self._get_owned_session(db, user_id, session_id)

        if session.status == InterviewSessionStatus.COMPLETED:
            return session

        questions = self.question_repo.get_by_session(db, session.id)
        answered = [question for question in questions if question.answer is not None]

        if not answered:
            raise ValueError("Cannot complete an interview with no answered questions")

        transcript = self._build_transcript(questions)

        summary_generation = self.ai.summarize_interview(target_role=session.target_role, transcript=transcript)
        summary = summary_generation.data

        feedback = InterviewFeedback(
            session_id=session.id,
            overall_score=summary.overall_score,
            summary=summary.summary,
            strengths=summary.strengths,
            weaknesses=summary.weaknesses,
            recommendation=summary.recommendation,
        )
        self.feedback_repo.create_feedback(db, feedback)

        roadmap_generation = self.ai.generate_roadmap(
            target_role=session.target_role,
            weaknesses=summary.weaknesses,
            summary=summary.summary,
        )
        roadmap = LearningRoadmap(
            session_id=session.id,
            items=[item.model_dump() for item in roadmap_generation.data.items],
        )
        self.roadmap_repo.create_roadmap(db, roadmap)

        session.overall_score = summary.overall_score
        session.completed_at = datetime.now(timezone.utc)
        self.session_repo.mark_completed(session)

        self.session_repo.commit(db)
        self.session_repo.refresh(db, session)

        return session

    @staticmethod
    def _build_transcript(questions : list[InterviewQuestion]) -> str:
        lines = []

        for question in questions:
            line = f"Q{question.order_index + 1} ({question.category}/{question.difficulty}): {question.question_text}"

            if question.answer is not None:
                line += f"\nAnswer: {question.answer.answer_text}\nScore: {question.answer.score}/100"
            else:
                line += "\nAnswer: (not answered)"

            lines.append(line)

        return "\n\n".join(lines)
