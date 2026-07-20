"""Execution context for orchestrator runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.orchestrator.errors import ExecutionError


@dataclass(slots=True)
class ExecutionContext:
    """Shared state passed between orchestrated agents."""

    request: str
    results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[ExecutionError] = field(default_factory=list)

    def set_result(
        self,
        agent_name: str,
        result: Any,
    ) -> None:
        """Store an agent result."""

        self.results[agent_name] = result

    def get_result(
        self,
        agent_name: str,
    ) -> Any:
        """Return a previously stored agent result."""

        return self.results[agent_name]

    def has_result(
        self,
        agent_name: str,
    ) -> bool:
        """Return True if a result exists."""

        return agent_name in self.results

    def add_error(
        self,
        error: ExecutionError,
    ) -> None:
        """Store a structured execution error."""

        self.errors.append(error)