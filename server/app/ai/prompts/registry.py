from app.ai.prompts.resume import ResumeAnalysisPrompt
from app.ai.prompts.interview import (
    InterviewQuestionGenerationPrompt,
    AnswerEvaluationPrompt,
    InterviewSummaryPrompt,
    LearningRoadmapPrompt,
)

class PromptRegistry:
    """central registry for all prompt builders"""

    @staticmethod
    def resume_analysis() -> ResumeAnalysisPrompt:
        return ResumeAnalysisPrompt()

    @staticmethod
    def interview_questions() -> InterviewQuestionGenerationPrompt:
        return InterviewQuestionGenerationPrompt()

    @staticmethod
    def answer_evaluation() -> AnswerEvaluationPrompt:
        return AnswerEvaluationPrompt()

    @staticmethod
    def interview_summary() -> InterviewSummaryPrompt:
        return InterviewSummaryPrompt()

    @staticmethod
    def learning_roadmap() -> LearningRoadmapPrompt:
        return LearningRoadmapPrompt()
