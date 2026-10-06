from typing import Any

from pydantic import SecretStr

from app.core.config import settings
from app.services.code_execution_service import (
    CodeExecutionService,
)


class StubResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "run": {
                "stdout": "42\n",
                "stderr": "",
                "code": 0,
            }
        }


class StubHttpClient:
    def __init__(
        self,
        captured_request: dict[str, Any],
        **options: Any,
    ) -> None:
        self.captured_request = captured_request
        self.captured_request["client_options"] = options

    def __enter__(self) -> "StubHttpClient":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None

    def post(
        self,
        url: str,
        **options: Any,
    ) -> StubResponse:
        self.captured_request["url"] = url
        self.captured_request["request_options"] = options

        return StubResponse()


def install_stub_client(
    monkeypatch,
    captured_request: dict[str, Any],
) -> None:
    def create_client(
        **options: Any,
    ) -> StubHttpClient:
        return StubHttpClient(
            captured_request,
            **options,
        )

    monkeypatch.setattr(
        "app.services.code_execution_service.httpx.Client",
        create_client,
    )


def test_code_execution_sends_configured_bearer_token(
    monkeypatch,
) -> None:
    captured_request: dict[str, Any] = {}

    monkeypatch.setattr(
        settings,
        "CODE_EXECUTION_AUTH_TOKEN",
        SecretStr("private-runner-token"),
    )

    install_stub_client(
        monkeypatch,
        captured_request,
    )

    service = CodeExecutionService()

    result = service.run(
        language="python",
        code="print(42)",
    )

    request_options = captured_request[
        "request_options"
    ]

    assert request_options["headers"] == {
        "Authorization": (
            "Bearer private-runner-token"
        )
    }
    assert request_options["json"]["language"] == (
        "python"
    )
    assert result.stdout == "42\n"
    assert result.exit_code == 0


def test_code_execution_omits_authentication_when_unconfigured(
    monkeypatch,
) -> None:
    captured_request: dict[str, Any] = {}

    monkeypatch.setattr(
        settings,
        "CODE_EXECUTION_AUTH_TOKEN",
        None,
    )

    install_stub_client(
        monkeypatch,
        captured_request,
    )

    service = CodeExecutionService()

    service.run(
        language="python",
        code="print(42)",
    )

    request_options = captured_request[
        "request_options"
    ]

    assert request_options["headers"] == {}