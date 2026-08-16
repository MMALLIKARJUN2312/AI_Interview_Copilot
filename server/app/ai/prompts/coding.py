from app.ai.prompts.base import BasePrompt

class DSACodingQuestionPrompt(BasePrompt):
    """Prompt builder for generating data-structures-and-algorithms coding
    questions, judged by input/output test cases (like a real coding round)."""

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
You are a senior interviewer running the data-structures-and-algorithms coding round
for a "{target_role}" interview loop.

Using the candidate's resume below, generate exactly {num_questions} standalone DSA
coding problems appropriate for a "{target_role}" at the seniority level implied by
the resume. Each problem must be solvable by reading input from stdin and writing the
result to stdout - like a real competitive-programming / online-assessment question,
NOT a "implement this function" signature problem.

For each question, provide 4-6 test cases covering the example case(s) plus edge cases.
Mark at least 2 of them as hidden (hidden: true) so the candidate cannot see the exact
edge cases in advance, but the visible ones must be enough to understand the problem.
Every input/expected_output must be exact stdin text and exact expected stdout text
(trimmed of trailing whitespace).
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
            "question": "full problem statement",
            "difficulty": "easy | medium | hard",
            "examples": "human-readable worked example(s)",
            "constraints": "e.g. 1 <= n <= 10^5",
            "test_cases": [
                {{"input": "", "expected_output": "", "hidden": false}}
            ]
        }}
    ]
}}
    """

class MachineCodingQuestionPrompt(BasePrompt):
    """Prompt builder for generating open-ended machine-coding / low-level-design
    tasks, evaluated holistically rather than by test cases."""

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
You are a senior interviewer running the machine-coding round for a "{target_role}"
interview loop. Machine coding means: build a small, working piece of software
(a class design, a mini-library, a simple in-memory system) in a fixed time window -
evaluated on correctness, design, and code quality, not a single pass/fail test.

Using the candidate's resume below, generate exactly {num_questions} machine-coding
tasks appropriate for a "{target_role}" at the seniority level implied by the resume
(e.g. "design and implement a rate limiter", "build an in-memory key-value store with
TTL support", "implement a parking lot management system"). Include the functional
requirements the solution must satisfy.
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
            "question": "full task description including functional requirements",
            "difficulty": "easy | medium | hard",
            "examples": "an example usage/interaction, if helpful",
            "constraints": "any explicit constraints or non-functional requirements",
            "test_cases": []
        }}
    ]
}}
    """

class CodeReviewPrompt(BasePrompt):
    """Prompt builder for evaluating a candidate's submitted code for a coding-round
    question - blends test-case results (when present) with code-quality review."""

    def build(
        self,
        *,
        target_role : str,
        round_type : str,
        question : str,
        language : str,
        code : str,
        test_summary : str | None = None,
    ) -> str:
        test_summary_section = (
            f"\nTest execution results :\n\n{test_summary}\n"
            if test_summary
            else "\nThis task has no automated test cases - evaluate the code purely on "
                 "correctness reasoning, design, and completeness.\n"
        )

        return f"""
You are a senior interviewer for the "{target_role}" {round_type.replace('_', ' ')} round,
reviewing a candidate's code submission.

Problem :

{question}

Candidate's Solution (language: {language}) :

```
{code}
```
{test_summary_section}
Evaluate as a real interviewer would: correctness, edge-case handling, time/space
complexity where relevant, code quality and readability. Be constructive but honest.
If test results are provided, they are the primary signal for correctness - the score
should reflect them, adjusted for code quality.

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
