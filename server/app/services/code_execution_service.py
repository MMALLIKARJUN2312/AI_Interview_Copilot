from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.constants import PISTON_RUNTIMES
from app.core.logger import logger

class CodeExecutionError(Exception):
    """Raised when the code execution backend itself is unreachable or errors -
    distinct from a candidate's own compile/runtime error, which is captured
    in stdout/stderr instead and is not an exception."""

@dataclass
class ExecutionOutcome:
    stdout : str
    stderr : str
    exit_code : int | None
    timed_out : bool

@dataclass
class TestCaseResult:
    input : str
    expected_output : str
    actual_output : str
    passed : bool
    stderr : str
    hidden : bool

class CodeExecutionService:
    """Executes untrusted candidate code via a Piston-compatible execution API
    (https://github.com/engineer-man/piston). All sandboxing happens on that
    service - this process never executes candidate code directly.
    """

    def __init__(self) -> None:
        self.base_url = settings.CODE_EXECUTION_API_URL.rstrip("/")
        self.timeout = settings.CODE_EXECUTION_TIMEOUT_SECONDS

    def run(self, language : str, code : str, stdin : str = "") -> ExecutionOutcome:
        runtime = PISTON_RUNTIMES.get(language)

        if runtime is None:
            raise CodeExecutionError(f"Unsupported language: {language}")

        payload = {
            "language": runtime["language"],
            "version": runtime["version"],
            "files": [{"content": code}],
            "stdin": stdin,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/execute", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as error:
            logger.error(
                "Piston HTTP error: status=%s body=%s",
                error.response.status_code,
                error.response.text[:1000],
            )

            raise CodeExecutionError(
                f"Piston returned HTTP {error.response.status_code}"
            ) from error

        except httpx.RequestError as error:
            logger.exception(
                "Could not connect to Piston: %s",
                error,
            )

            raise CodeExecutionError(
                "Could not connect to code execution service"
            ) from error

        run_result = data.get("run") or {}
        compile_result = data.get("compile")

        stderr_parts = []
        if compile_result and compile_result.get("stderr"):
            stderr_parts.append(compile_result["stderr"])
        if run_result.get("stderr"):
            stderr_parts.append(run_result["stderr"])

        return ExecutionOutcome(
            stdout=run_result.get("stdout", ""),
            stderr="\n".join(stderr_parts),
            exit_code=run_result.get("code"),
            timed_out=run_result.get("signal") == "SIGKILL",
        )

    def run_test_cases(
        self,
        language : str,
        code : str,
        test_cases : list[dict],
    ) -> list[TestCaseResult]:
        results = []

        for case in test_cases:
            outcome = self.run(language, code, stdin=case["input"])
            actual = outcome.stdout.strip()
            expected = case["expected_output"].strip()
            passed = actual == expected and not outcome.stderr and not outcome.timed_out

            results.append(
                TestCaseResult(
                    input=case["input"],
                    expected_output=case["expected_output"],
                    actual_output=actual,
                    passed=passed,
                    stderr=outcome.stderr,
                    hidden=case.get("hidden", False),
                )
            )

        return results
