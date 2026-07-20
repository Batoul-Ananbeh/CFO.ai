"""Structured error models for orchestrator execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionError:
    """Describe an error raised while executing an agent."""

    agent_name: str
    message: str
    exception_type: str

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

        return cls(
            agent_name=normalized_agent_name,
            message=message,
            exception_type=type(exception).__name__,
        )

    @staticmethod
    def _normalize_required_text(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """Validate and normalize a required text value."""

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized_value