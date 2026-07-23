"""Structured error models for orchestrator execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ValidationError

from src.ai.errors import (
    AIProviderError,
    AIProviderResponseError,
)


class ExecutionErrorCategory(StrEnum):
    """Stable categories used to classify execution failures."""

    VALIDATION = "VALIDATION"

    AI_AUTHENTICATION = "AI_AUTHENTICATION"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    AI_PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
    AI_PROVIDER_RESPONSE = "AI_PROVIDER_RESPONSE"
    AI_PROVIDER = "AI_PROVIDER"

    DEPENDENCY = "DEPENDENCY"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True, slots=True)
class ExecutionError:
    """Describe an error raised while executing an agent."""

    agent_name: str
    message: str
    exception_type: str

    category: ExecutionErrorCategory = (
        ExecutionErrorCategory.INTERNAL
    )

    provider_status_code: int | None = None
    retryable: bool = False

    @classmethod
    def from_exception(
        cls,
        *,
        agent_name: str,
        exception: Exception,
    ) -> "ExecutionError":
        """Create a structured execution error from an exception."""

        normalized_agent_name = cls._normalize_required_text(
            agent_name,
            field_name="Agent name",
        )

        message = str(exception).strip()

        if not message:
            message = "An unexpected error occurred."

        (
            category,
            provider_status_code,
            retryable,
        ) = cls._classify_exception(
            agent_name=normalized_agent_name,
            exception=exception,
            message=message,
        )

        return cls(
            agent_name=normalized_agent_name,
            message=message,
            exception_type=type(exception).__name__,
            category=category,
            provider_status_code=provider_status_code,
            retryable=retryable,
        )

    @staticmethod
    def _classify_exception(
        *,
        agent_name: str,
        exception: Exception,
        message: str,
    ) -> tuple[
        ExecutionErrorCategory,
        int | None,
        bool,
    ]:
        """Classify an exception for application and API handling."""

        if isinstance(
            exception,
            AIProviderResponseError,
        ):
            return (
                ExecutionErrorCategory.AI_PROVIDER_RESPONSE,
                exception.status_code,
                exception.retryable,
            )

        if isinstance(
            exception,
            AIProviderError,
        ):
            status_code = exception.status_code
            retryable = exception.retryable

            if status_code in {401, 403}:
                category = (
                    ExecutionErrorCategory.AI_AUTHENTICATION
                )

            elif status_code == 429:
                category = (
                    ExecutionErrorCategory.AI_RATE_LIMIT
                )

            elif (
                retryable
                or status_code
                in {
                    408,
                    409,
                    425,
                    500,
                    502,
                    503,
                    504,
                }
            ):
                category = (
                    ExecutionErrorCategory
                    .AI_PROVIDER_UNAVAILABLE
                )

            else:
                category = (
                    ExecutionErrorCategory.AI_PROVIDER
                )

            return (
                category,
                status_code,
                retryable,
            )

        if (
            agent_name == "deterministic_finance"
            and isinstance(
                exception,
                (
                    ValidationError,
                    TypeError,
                    ValueError,
                ),
            )
        ):
            return (
                ExecutionErrorCategory.VALIDATION,
                None,
                False,
            )

        if "missing required inputs" in message.lower():
            return (
                ExecutionErrorCategory.DEPENDENCY,
                None,
                False,
            )

        return (
            ExecutionErrorCategory.INTERNAL,
            None,
            False,
        )

    @staticmethod
    def _normalize_required_text(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """Validate and normalize a required text value."""

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized_value