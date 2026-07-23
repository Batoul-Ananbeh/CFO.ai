"""Configuration for the CFO.ai AI layer."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _read_int(
    variable_name: str,
    default: int,
) -> int:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{variable_name} must be a valid integer."
        ) from exc


def _read_float(
    variable_name: str,
    default: float,
) -> float:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{variable_name} must be a valid number."
        ) from exc


@dataclass(frozen=True, slots=True)
class AISettings:
    """Environment-backed AI configuration."""

    provider: str = "google"
    model: str = "gemini-3.6-flash"
    temperature: float = 0.0
    api_key: str | None = None
    timeout_ms: int = 60_000
    retry_attempts: int = 4
    max_output_tokens: int = 2_048

    @classmethod
    def from_env(cls) -> "AISettings":
        provider = os.getenv(
            "AI_PROVIDER",
            "google",
        ).strip().lower()

        model = os.getenv(
            "AI_MODEL",
            "gemini-3.6-flash",
        ).strip()

        api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        return cls(
            provider=provider,
            model=model,
            temperature=_read_float(
                "AI_TEMPERATURE",
                0.0,
            ),
            api_key=api_key,
            timeout_ms=_read_int(
                "AI_TIMEOUT_MS",
                60_000,
            ),
            retry_attempts=_read_int(
                "AI_RETRY_ATTEMPTS",
                4,
            ),
            max_output_tokens=_read_int(
                "AI_MAX_OUTPUT_TOKENS",
                2_048,
            ),
        )

    def validate(self) -> None:
        """Validate configuration before an external LLM call."""

        if self.provider != "google":
            raise ValueError(
                f"Unsupported AI provider: {self.provider!r}. "
                "Currently supported provider: 'google'."
            )

        if not self.model:
            raise ValueError("AI_MODEL cannot be empty.")

        if not 0 <= self.temperature <= 2:
            raise ValueError(
                "AI_TEMPERATURE must be between 0 and 2."
            )

        if self.timeout_ms <= 0:
            raise ValueError(
                "AI_TIMEOUT_MS must be greater than zero."
            )

        if self.retry_attempts < 1:
            raise ValueError(
                "AI_RETRY_ATTEMPTS must be at least 1."
            )

        if self.max_output_tokens < 1:
            raise ValueError(
                "AI_MAX_OUTPUT_TOKENS must be at least 1."
            )

        if not self.api_key:
            raise ValueError(
                "Missing GOOGLE_API_KEY or GEMINI_API_KEY."
            )
