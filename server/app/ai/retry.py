"""Retry policies used by the AI platform"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from app.ai.exceptions import AIProviderError

retry_ai_request = retry(
    retry=retry_if_exception_type(AIProviderError),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)