import json
import re

from app.ai.exceptions import AIResponseParsingError


class AIResponseParser:
    """Converts raw LLM responses to Python dictionaries."""

    @staticmethod
    def parse_json(raw_response: str) -> dict:
        if not raw_response:
            raise AIResponseParsingError("Received empty AI response")

        cleaned = raw_response.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)

        except json.JSONDecodeError as exc:
            # LLMs occasionally emit LaTeX-style backslashes inside JSON
            # strings, e.g. "\ge", "\le", "\alpha".
            # These are invalid JSON escapes.
            repaired = re.sub(
                r'\\(?!["\\/bfnrtu])',
                r"\\\\",
                cleaned,
            )

            try:
                result = json.loads(repaired)
            except json.JSONDecodeError:
                raise AIResponseParsingError(
                    f"Unable to parse AI response into JSON. "
                    f"Line {exc.lineno}, column {exc.colno}, "
                    f"position {exc.pos}. "
                    f"Problematic section: {cleaned[max(0, exc.pos - 150):exc.pos + 300]!r}"
                ) from exc

        if not isinstance(result, dict):
            raise AIResponseParsingError(
                "AI response must be a JSON object"
            )

        return result
