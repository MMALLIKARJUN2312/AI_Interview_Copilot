from typing import Callable

import httpx
from google import genai

from app.ai.constants import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_SECONDS
from app.ai.exceptions import AIProviderError
from app.ai.provider import AIProvider
from app.ai.retry import retry_ai_request
from app.core.config import settings
from app.core.logger import logger

class GeminiProvider(AIProvider):
    """Gemini implementation of the AIProvider interface"""

    name = "gemini"

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("GEMINI_API_KEY is required to use the gemini provider")

        self.model = settings.GEMINI_MODEL
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @retry_ai_request
    def generate(self, prompt : str) -> str:
        try:
            logger.info("Sending request to the Gemini model: %s", self.model)
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            if response.text is None:
                raise AIProviderError("Gemini returned an empty response")

            logger.info("Gemini request completed successfully")

            return response.text

        except Exception as exc:
            logger.exception("Gemini request failed")
            raise AIProviderError("Failed to communicate with the AI provider") from exc

class OpenAICompatibleProvider(AIProvider):
    """Adapter for providers exposing an OpenAI-compatible
    Chat Completions API.
    """

    def __init__(self, *, name : str, model : str, base_url : str, api_key : str | None) -> None:
        if not api_key:
            raise AIProviderError(f"An API key is required to use the {name} provider")

        self.name = name
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @retry_ai_request
    def generate(self, prompt : str) -> str:
        try:
            logger.info("Sending request to %s model: %s", self.name, self.model)
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": DEFAULT_TEMPERATURE,
                },
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            if not content:
                raise AIProviderError(f"{self.name} returned an empty response")

            logger.info("%s request completed successfully", self.name)

            return content

        except AIProviderError:
            raise
        except Exception as exc:
            logger.exception("%s request failed", self.name)
            raise AIProviderError(f"Failed to communicate with {self.name}") from exc

class FailoverAIProvider(AIProvider):
    """Tries each configured provider in order, falling through to the next
    on failure. After a successful call, `name`/`model` reflect whichever
    provider actually served it, so callers persisting that metadata (e.g.
    AIClient.generate_structured) see the true source.
    """

    def __init__(self, providers : list[AIProvider]) -> None:
        if not providers:
            raise AIProviderError("At least one AI provider must be configured")

        self.providers = providers
        self.name = providers[0].name
        self.model = providers[0].model

    def generate(self, prompt : str) -> str:
        last_error : Exception | None = None

        for provider in self.providers:
            try:
                result = provider.generate(prompt)
                self.name = provider.name
                self.model = provider.model
                return result
            except AIProviderError as error:
                logger.warning("AI provider '%s' failed, trying next in chain: %s", provider.name, error)
                last_error = error

        raise AIProviderError("All configured AI providers failed") from last_error

PROVIDER_BUILDERS : dict[str, Callable[[], AIProvider]] = {
    "gemini": GeminiProvider,
    "groq": lambda: OpenAICompatibleProvider(
        name="groq", model=settings.GROQ_MODEL,
        base_url="https://api.groq.com/openai/v1", api_key=settings.GROQ_API_KEY,
    ),
    "openrouter": lambda: OpenAICompatibleProvider(
        name="openrouter", model=settings.OPENROUTER_MODEL,
        base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY,
    ),
}

def build_ai_provider_chain() -> AIProvider:
    """Builds the configured AI_PROVIDER_CHAIN into a single AIProvider -
    the provider itself when only one is configured, or a FailoverAIProvider
    that tries each in order when more than one is.
    """
    keys = [key.strip().lower() for key in settings.AI_PROVIDER_CHAIN.split(",") if key.strip()]

    if not keys:
        raise AIProviderError("AI_PROVIDER_CHAIN must configure at least one provider")

    providers = []
    for key in keys:
        builder = PROVIDER_BUILDERS.get(key)

        if builder is None:
            raise AIProviderError(
                f"Unknown AI provider '{key}' in AI_PROVIDER_CHAIN; "
                f"supported providers are {sorted(PROVIDER_BUILDERS)}"
            )

        providers.append(builder())

    return providers[0] if len(providers) == 1 else FailoverAIProvider(providers)
