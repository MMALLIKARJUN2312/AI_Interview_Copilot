from app.ai.client import AIClient, GeminiProvider
from app.ai.models import (
    AIGenerationResult,
    ResumeAnalysisResult,
    InterviewQuestionSetResult,
    AnswerEvaluationResult,
    InterviewSummaryResult,
    LearningRoadmapResult,
    CodingQuestionSetResult,
)
from app.ai.prompts.registry import PromptRegistry

class AIOrchestrator:
    """Coordinates end-end to AI workflows

    Responsibilities: Build prompts, Invoke AI providers, Parse responses, Validate responses
    """

    def __init__(self) -> None:
        self.client = AIClient(provider=GeminiProvider())

    def analyze_resume(
        self,
        resume_text : str,
        target_role : str,
        job_description : str | None = None,
    ) -> AIGenerationResult[ResumeAnalysisResult]:
        prompt = PromptRegistry.resume_analysis().build(
            resume_text=resume_text,
            target_role=target_role,
            job_description=job_description,
        )

        return self.client.generate_structured(prompt=prompt, response_model=ResumeAnalysisResult)

    def generate_interview_questions(
        self,
        resume_text : str,
        target_role : str,
        num_questions : int,
        job_description : str | None = None,
    ) -> AIGenerationResult[InterviewQuestionSetResult]:
        prompt = PromptRegistry.interview_questions().build(
            resume_text=resume_text,
            target_role=target_role,
            num_questions=num_questions,
            job_description=job_description,
        )

        return self.client.generate_structured(prompt=prompt, response_model=InterviewQuestionSetResult)

    def evaluate_answer(
        self,
        target_role : str,
        question : str,
        category : str,
        difficulty : str,
        answer : str,
    ) -> AIGenerationResult[AnswerEvaluationResult]:
        prompt = PromptRegistry.answer_evaluation().build(
            target_role=target_role,
            question=question,
            category=category,
            difficulty=difficulty,
            answer=answer,
        )

        return self.client.generate_structured(prompt=prompt, response_model=AnswerEvaluationResult)

    def summarize_interview(
        self,
        target_role : str,
        transcript : str,
    ) -> AIGenerationResult[InterviewSummaryResult]:
        prompt = PromptRegistry.interview_summary().build(target_role=target_role, transcript=transcript)

        return self.client.generate_structured(prompt=prompt, response_model=InterviewSummaryResult)

    def generate_roadmap(
        self,
        target_role : str,
        weaknesses : list[str],
        summary : str,
    ) -> AIGenerationResult[LearningRoadmapResult]:
        prompt = PromptRegistry.learning_roadmap().build(
            target_role=target_role,
            weaknesses=weaknesses,
            summary=summary,
        )

        return self.client.generate_structured(prompt=prompt, response_model=LearningRoadmapResult)

    def generate_dsa_questions(
        self,
        resume_text : str,
        target_role : str,
        num_questions : int,
        job_description : str | None = None,
    ) -> AIGenerationResult[CodingQuestionSetResult]:
        prompt = PromptRegistry.dsa_coding_question().build(
            resume_text=resume_text,
            target_role=target_role,
            num_questions=num_questions,
            job_description=job_description,
        )

        return self.client.generate_structured(prompt=prompt, response_model=CodingQuestionSetResult)

    def generate_machine_coding_questions(
        self,
        resume_text : str,
        target_role : str,
        num_questions : int,
        job_description : str | None = None,
    ) -> AIGenerationResult[CodingQuestionSetResult]:
        prompt = PromptRegistry.machine_coding_question().build(
            resume_text=resume_text,
            target_role=target_role,
            num_questions=num_questions,
            job_description=job_description,
        )

        return self.client.generate_structured(prompt=prompt, response_model=CodingQuestionSetResult)

    def evaluate_code(
        self,
        target_role : str,
        round_type : str,
        question : str,
        language : str,
        code : str,
        test_summary : str | None = None,
    ) -> AIGenerationResult[AnswerEvaluationResult]:
        prompt = PromptRegistry.code_review().build(
            target_role=target_role,
            round_type=round_type,
            question=question,
            language=language,
            code=code,
            test_summary=test_summary,
        )

        return self.client.generate_structured(prompt=prompt, response_model=AnswerEvaluationResult)
