MAX_RESUME_SIZE = 5

ALLOWED_RESUME_TYPES = ["application/pdf"]
PDF_MAGIC_BYTES = b"%PDF-"

DEFAULT_INTERVIEW_QUESTION_COUNT = 5
MIN_INTERVIEW_QUESTIONS = 3
MAX_INTERVIEW_QUESTIONS = 10

VALID_QUESTION_CATEGORIES = {"technical", "behavioral", "system_design"}
VALID_QUESTION_DIFFICULTIES = {"easy", "medium", "hard"}
DEFAULT_QUESTION_CATEGORY = "technical"
DEFAULT_QUESTION_DIFFICULTY = "medium"

VALID_ROUND_TYPES = {"dsa_coding", "machine_coding", "general"}
DEFAULT_ROUND_TYPE = "general"
MAX_QUESTIONS_PER_ROUND = 5

# A realistic default mock-interview loop when the candidate doesn't customize rounds.
DEFAULT_ROUND_COMPOSITION = [
    {"round_type": "dsa_coding", "num_questions": 2},
    {"round_type": "machine_coding", "num_questions": 1},
    {"round_type": "general", "num_questions": 2},
]

VALID_CODE_LANGUAGES = {"python", "javascript", "java", "cpp"}
DEFAULT_CODE_LANGUAGE = "python"

PISTON_RUNTIMES = {
    "python": {
        "language": "python",
        "version": "3.12.0",
    },
    "javascript": {
        "language": "javascript",
        "version": "20.11.1",
    },
    "java": {
        "language": "java",
        "version": "15.0.2",
    },
    "cpp": {
        "language": "c++",
        "version": "10.2.0",
    },
}
