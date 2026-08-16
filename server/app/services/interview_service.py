from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.orchestrator import AIOrchestrator
from app.core.constants import (
    VALID_QUESTION_CATEGORIES,
    VALID_QUESTION_DIFFICULTIES,
    DEFAULT_QUESTION_CATEGORY,
    DEFAULT_QUESTION_DIFFICULTY,
    VALID_CODE_LANGUAGES,
    DEFAULT_CODE_LANGUAGE,
)
from app.models.interview import (
    InterviewSession,
    InterviewSessionStatus,
    InterviewQuestion,
    RoundType,
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
from app.services.code_execution_service import CodeExecutionService, CodeExecutionError, TestCaseResult

def _normalize(value : str, valid_values : set[str], default : str) -> str:
    normalized = (value or "").strip().lower().replace(" ", "_")
    return normalized if normalized in valid_values else default

class InterviewService:
    """Orchestrates the full lifecycle of a role-aligned mock interview session:
    generating a multi-round question set (DSA coding, machine coding, and
    general/behavioral rounds) from a resume, running and evaluating candidate
    answers - including executing submitted code against test cases - and
    producing end-of-session feedback and a learning roadmap.
    """

    def __init__(self) -> None:
        self.ai = AIOrchestrator()
        self.code_execution = CodeExecutionService()
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
        rounds : list[dict],
    ) -> InterviewSession:
        resume = self.resume_repo.get_by_id(db, resume_id)

        if resume is None or resume.user_id != user_id:
            raise ValueError("Resume not found")

        if not resume.extracted_text:
            raise ValueError("This resume has no extracted text yet; re-upload and analyze it first")

        if not rounds:
            raise ValueError("At least one interview round must be configured")

        questions : list[InterviewQuestion] = []
        order_index = 0
        provider = None
        model = None

        for round_config in rounds:
            round_type = round_config["round_type"]
            num_questions = round_config["num_questions"]

            if round_type == RoundType.DSA_CODING.value:
                generation = self.ai.generate_dsa_questions(
                    resume_text=resume.extracted_text,
                    target_role=resume.target_role,
                    num_questions=num_questions,
                    job_description=resume.job_description,
                )
                for item in generation.data.questions:
                    questions.append(InterviewQuestion(
                        order_index=order_index,
                        question_text=item.question,
                        category="coding",
                        difficulty=_normalize(item.difficulty, VALID_QUESTION_DIFFICULTIES, DEFAULT_QUESTION_DIFFICULTY),
                        round_type=RoundType.DSA_CODING,
                        examples=item.examples or None,
                        constraints=item.constraints or None,
                        test_cases=[tc.model_dump() for tc in item.test_cases],
                    ))
                    order_index += 1
                provider, model = generation.provider, generation.model

            elif round_type == RoundType.MACHINE_CODING.value:
                generation = self.ai.generate_machine_coding_questions(
                    resume_text=resume.extracted_text,
                    target_role=resume.target_role,
                    num_questions=num_questions,
                    job_description=resume.job_description,
                )
                for item in generation.data.questions:
                    questions.append(InterviewQuestion(
                        order_index=order_index,
                        question_text=item.question,
                        category="coding",
                        difficulty=_normalize(item.difficulty, VALID_QUESTION_DIFFICULTIES, DEFAULT_QUESTION_DIFFICULTY),
                        round_type=RoundType.MACHINE_CODING,
                        examples=item.examples or None,
                        constraints=item.constraints or None,
                        test_cases=[],
                    ))
                    order_index += 1
                provider, model = generation.provider, generation.model

            else:
                generation = self.ai.generate_interview_questions(
                    resume_text=resume.extracted_text,
                    target_role=resume.target_role,
                    num_questions=num_questions,
                    job_description=resume.job_description,
                )
                for item in generation.data.questions:
                    questions.append(InterviewQuestion(
                        order_index=order_index,
                        question_text=item.question,
                        category=_normalize(item.category, VALID_QUESTION_CATEGORIES, DEFAULT_QUESTION_CATEGORY),
                        difficulty=_normalize(item.difficulty, VALID_QUESTION_DIFFICULTIES, DEFAULT_QUESTION_DIFFICULTY),
                        round_type=RoundType.GENERAL,
                    ))
                    order_index += 1
                provider, model = generation.provider, generation.model

        if not questions:
            raise ValueError("The AI provider did not return any interview questions")

        session = InterviewSession(
            user_id=user_id,
            resume_id=resume.id,
            target_role=resume.target_role,
            status=InterviewSessionStatus.IN_PROGRESS,
            total_questions=len(questions),
            current_index=0,
            provider=provider,
            model=model,
        )
        self.session_repo.create_session(db, session)
        self.session_repo.flush(db)

        for question in questions:
            question.session_id = session.id
        self.question_repo.create_questions(db, questions)

        self.session_repo.commit(db)
        self.session_repo.refresh(db, session)

        return session

    def get_next_question(self, db : Session, user_id : int, session_id : int) -> InterviewQuestion | None:
        session = self._get_owned_session(db, user_id, session_id)

        return self.question_repo.get_next_unanswered(db, session.id)

    def _get_answerable_question(
        self, db : Session, session : InterviewSession, question_id : int
    ) -> InterviewQuestion:
        if session.status != InterviewSessionStatus.IN_PROGRESS:
            raise ValueError("This interview session is not in progress")

        question = self.question_repo.get_by_id(db, question_id)

        if question is None or question.session_id != session.id:
            raise ValueError("Question not found in this session")

        if self.answer_repo.get_by_question(db, question.id) is not None:
            raise ValueError("This question has already been answered")

        return question

    def run_code(
        self,
        db : Session,
        user_id : int,
        session_id : int,
        question_id : int,
        code : str,
        language : str,
    ) -> list[TestCaseResult]:
        session = self._get_owned_session(db, user_id, session_id)
        question = self._get_answerable_question(db, session, question_id)

        if question.round_type == RoundType.GENERAL:
            raise ValueError("This question does not support code execution")

        language = _normalize(language, VALID_CODE_LANGUAGES, DEFAULT_CODE_LANGUAGE)
        visible_cases = [case for case in (question.test_cases or []) if not case.get("hidden")]

        try:
            if visible_cases:
                return self.code_execution.run_test_cases(language, code, visible_cases)

            outcome = self.code_execution.run(language, code, stdin="")
            return [TestCaseResult(
                input="",
                expected_output="(no automated test cases for this task - review your output manually)",
                actual_output=outcome.stdout.strip(),
                passed=not outcome.stderr and not outcome.timed_out,
                stderr=outcome.stderr,
                hidden=False,
            )]
        except CodeExecutionError as error:
            raise ValueError(str(error))

    def submit_answer(
        self,
        db : Session,
        user_id : int,
        session_id : int,
        question_id : int,
        answer_text : str | None = None,
        code : str | None = None,
        language : str | None = None,
    ) -> InterviewAnswer:
        session = self._get_owned_session(db, user_id, session_id)
        question = self._get_answerable_question(db, session, question_id)

        if question.round_type == RoundType.GENERAL:
            if not answer_text or not answer_text.strip():
                raise ValueError("An answer is required for this question")
            answer = self._submit_general_answer(session, question, answer_text)
        else:
            if not code or not code.strip():
                raise ValueError("Code is required for this question")
            language = _normalize(language or "", VALID_CODE_LANGUAGES, DEFAULT_CODE_LANGUAGE)
            answer = self._submit_code_answer(session, question, code, language)

        self.answer_repo.create_answer(db, answer)

        session.current_index += 1

        self.session_repo.commit(db)
        self.session_repo.refresh(db, answer)

        return answer

    def _submit_general_answer(
        self, session : InterviewSession, question : InterviewQuestion, answer_text : str
    ) -> InterviewAnswer:
        generation = self.ai.evaluate_answer(
            target_role=session.target_role,
            question=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
            answer=answer_text,
        )
        result = generation.data

        return InterviewAnswer(
            question_id=question.id,
            answer_text=answer_text,
            score=result.score,
            feedback=result.feedback,
            strengths=result.strengths,
            improvements=result.improvements,
        )

    def _submit_code_answer(
        self, session : InterviewSession, question : InterviewQuestion, code : str, language : str
    ) -> InterviewAnswer:
        test_cases = question.test_cases or []
        test_results : list[TestCaseResult] = []
        passed_count = None
        total_count = None
        test_summary = None

        if test_cases:
            try:
                test_results = self.code_execution.run_test_cases(language, code, test_cases)
            except CodeExecutionError as error:
                raise ValueError(str(error))

            passed_count = sum(1 for result in test_results if result.passed)
            total_count = len(test_results)
            test_summary = "\n".join(
                f"Test {index + 1}: {'PASSED' if result.passed else 'FAILED'}"
                + (f" - stderr: {result.stderr[:200]}" if result.stderr else "")
                for index, result in enumerate(test_results)
            )

        review = self.ai.evaluate_code(
            target_role=session.target_role,
            round_type=question.round_type.value,
            question=question.question_text,
            language=language,
            code=code,
            test_summary=test_summary,
        )
        ai_score = review.data.score

        if total_count:
            test_score = round(100 * passed_count / total_count)
            score = round(0.7 * test_score + 0.3 * ai_score)
        else:
            score = ai_score

        execution_results = [
            {
                "input": result.input,
                "expected_output": result.expected_output,
                "actual_output": result.actual_output,
                "passed": result.passed,
                "stderr": result.stderr,
                "hidden": result.hidden,
            }
            for result in test_results
        ] or None

        return InterviewAnswer(
            question_id=question.id,
            answer_text=code,
            score=score,
            feedback=review.data.feedback,
            strengths=review.data.strengths,
            improvements=review.data.improvements,
            language=language,
            execution_results=execution_results,
            passed_test_count=passed_count,
            total_test_count=total_count,
        )

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
            round_label = question.round_type.value if hasattr(question.round_type, "value") else question.round_type
            line = f"Q{question.order_index + 1} [{round_label}] ({question.category}/{question.difficulty}): {question.question_text}"

            if question.answer is not None:
                if question.round_type == RoundType.GENERAL:
                    line += f"\nAnswer: {question.answer.answer_text}\nScore: {question.answer.score}/100"
                else:
                    test_note = (
                        f", tests passed {question.answer.passed_test_count}/{question.answer.total_test_count}"
                        if question.answer.total_test_count
                        else ""
                    )
                    line += (
                        f"\nSubmitted code ({question.answer.language}){test_note}"
                        f"\nScore: {question.answer.score}/100"
                    )
            else:
                line += "\nAnswer: (not answered)"

            lines.append(line)

        return "\n\n".join(lines)
