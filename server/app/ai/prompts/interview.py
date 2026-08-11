from app.ai.prompts.base import BasePrompt

class InterviewQuestionGenerationPrompt(BasePrompt):
    """Prompt builder for generating role-aligned mock interview questions"""

    def build(
        self,
        *,
        resume_text : str,
        target_role : str,
        num_questions : int,
        job_description : str | None = None,
    ) -> str:
        job_description_section = (
            f"\nTarget Job Description :\n\n{job_description}\n"
            if job_description
            else ""
        )

        return f"""
You are a senior technical interviewer and hiring manager conducting a real interview
for the role of "{target_role}".

Using the candidate's resume below, generate exactly {num_questions} interview questions
that a real "{target_role}" interview panel would ask THIS candidate. Base the questions on:
- The specific skills, technologies, and projects mentioned in the resume
- The core competencies expected for a "{target_role}" at the seniority level implied by the resume
- A realistic mix of technical, behavioral, and (if applicable) system-design questions

Do not ask generic questions unrelated to "{target_role}" or to this resume.
{job_description_section}
Return only valid JSON.

Do Not include markdown.

Do Not include explanations.

Resume :

{resume_text}

Expected format :

{{
    "questions": [
        {{
            "question": "",
            "category": "technical | behavioral | system_design",
            "difficulty": "easy | medium | hard"
        }}
    ]
}}
    """

class AnswerEvaluationPrompt(BasePrompt):
    """Prompt builder for evaluating a candidate's answer to an interview question"""

    def build(
        self,
        *,
        target_role : str,
        question : str,
        category : str,
        difficulty : str,
        answer : str,
    ) -> str:
        return f"""
You are a senior technical interviewer for the role of "{target_role}", evaluating a
candidate's spoken/written answer to the following interview question.

Question ({category}, {difficulty}) :

{question}

Candidate's Answer :

{answer}

Evaluate the answer as a real "{target_role}" interviewer would: correctness, depth,
clarity, and relevance to the role. Be constructive but honest.

Return only valid JSON.

Do Not include markdown.

Do Not include explanations.

Expected format :

{{
    "score": 0,
    "feedback": "",
    "strengths": [],
    "improvements": []
}}
    """

class InterviewSummaryPrompt(BasePrompt):
    """Prompt builder for the end-of-session interview summary"""

    def build(self, *, target_role : str, transcript : str) -> str:
        return f"""
You are a senior hiring manager for the role of "{target_role}", writing the final
debrief after a mock interview. Below is the full transcript of questions, the
candidate's answers, and per-answer scores.

Transcript :

{transcript}

Summarize the candidate's overall performance for a "{target_role}" position: give an
overall score, a written summary, key strengths, key weaknesses, and a hiring
recommendation.

Return only valid JSON.

Do Not include markdown.

Do Not include explanations.

Expected format :

{{
    "overall_score": 0,
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "recommendation": ""
}}
    """

class LearningRoadmapPrompt(BasePrompt):
    """Prompt builder for generating a personalized learning roadmap"""

    def build(self, *, target_role : str, weaknesses : list[str], summary : str) -> str:
        weaknesses_text = "\n".join(f"- {item}" for item in weaknesses) or "- None identified"

        return f"""
You are a career coach helping a candidate prepare for a "{target_role}" role.

Interview Summary :

{summary}

Identified Weaknesses :

{weaknesses_text}

Create a personalized, prioritized learning roadmap that will close these gaps and get
this candidate ready to succeed in a real "{target_role}" interview and job.

Return only valid JSON.

Do Not include markdown.

Do Not include explanations.

Expected format :

{{
    "items": [
        {{
            "topic": "",
            "description": "",
            "priority": "high | medium | low",
            "resources": []
        }}
    ]
}}
    """
