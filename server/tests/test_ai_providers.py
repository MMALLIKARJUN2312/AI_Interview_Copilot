import pytest

from app.ai.exceptions import AIProviderError
from app.ai.provider import AIProvider
from app.ai.providers import (
    OpenAICompatibleProvider,
    FailoverAIProvider,
    build_ai_provider_chain,
    PROVIDER_BUILDERS,
)


class StubProvider(AIProvider):
    """A minimal AIProvider double with no retry decorator, so failure-path
    tests run instantly instead of waiting through real tenacity backoff."""

    def __init__(self, name, *, fails=False):
        self.name = name
        self.model = f"{name}-model"
        self.fails = fails
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        if self.fails:
            raise AIProviderError(f"{self.name} is down")
        return f"response from {self.name}"


def test_openai_compatible_provider_requires_api_key():
    with pytest.raises(AIProviderError, match="API key"):
        OpenAICompatibleProvider(name="groq", model="m", base_url="https://example.com", api_key=None)


def test_openai_compatible_provider_parses_chat_completion_response(monkeypatch):
    provider = OpenAICompatibleProvider(
        name="groq", model="openai/gpt-oss-120b",
        base_url="https://api.groq.com/openai/v1", api_key="fake-key",
    )

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "hello from groq"}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("app.ai.providers.httpx.post", fake_post)

    result = provider.generate("say hi")

    assert result == "hello from groq"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer fake-key"
    assert captured["json"]["model"] == "openai/gpt-oss-120b"
    assert captured["json"]["messages"] == [{"role": "user", "content": "say hi"}]


def test_failover_tries_next_provider_on_failure():
    primary = StubProvider("primary", fails=True)
    secondary = StubProvider("secondary", fails=False)
    failover = FailoverAIProvider([primary, secondary])

    result = failover.generate("prompt")

    assert result == "response from secondary"
    assert primary.calls == 1
    assert secondary.calls == 1
    # metadata reflects whichever provider actually served the request
    assert failover.name == "secondary"
    assert failover.model == "secondary-model"


def test_failover_raises_when_every_provider_fails():
    providers = [StubProvider("a", fails=True), StubProvider("b", fails=True)]
    failover = FailoverAIProvider(providers)

    with pytest.raises(AIProviderError, match="All configured AI providers failed"):
        failover.generate("prompt")

    assert all(provider.calls == 1 for provider in providers)


def test_failover_does_not_call_later_providers_once_one_succeeds():
    first = StubProvider("first", fails=False)
    unused = StubProvider("unused", fails=False)
    failover = FailoverAIProvider([first, unused])

    failover.generate("prompt")

    assert first.calls == 1
    assert unused.calls == 0


def test_build_ai_provider_chain_single_provider_returns_it_directly(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER_CHAIN", "gemini")
    monkeypatch.setattr("app.ai.providers.settings.GEMINI_API_KEY", "fake-key")

    provider = build_ai_provider_chain()

    assert provider.name == "gemini"
    assert not isinstance(provider, FailoverAIProvider)


def test_build_ai_provider_chain_multiple_providers_wraps_in_failover(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER_CHAIN", "gemini,groq")
    monkeypatch.setattr("app.ai.providers.settings.GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr("app.ai.providers.settings.GROQ_API_KEY", "fake-key")

    provider = build_ai_provider_chain()

    assert isinstance(provider, FailoverAIProvider)
    assert [p.name for p in provider.providers] == ["gemini", "groq"]


def test_build_ai_provider_chain_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER_CHAIN", "not-a-real-provider")

    with pytest.raises(AIProviderError, match="Unknown AI provider"):
        build_ai_provider_chain()


def test_build_ai_provider_chain_requires_api_key_for_listed_provider(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER_CHAIN", "groq")
    monkeypatch.setattr("app.ai.providers.settings.GROQ_API_KEY", None)

    with pytest.raises(AIProviderError, match="API key"):
        build_ai_provider_chain()


def test_all_builtin_providers_are_registered():
    assert set(PROVIDER_BUILDERS) == {"gemini", "groq", "openrouter"}
