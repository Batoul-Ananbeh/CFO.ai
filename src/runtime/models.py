"""Result models for the unified CFO runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.orchestrator.errors import ExecutionError


class HybridRuntimeStatus(StrEnum):
    """Final status of one unified CFO runtime execution."""

    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class HybridRuntimeResult:
    """Unified output from deterministic and AI finance layers."""

    request: str
    execution_plan: tuple[str, ...]
    executed_agents: tuple[str, ...]
    verified_results: dict[str, Any]
    ai_results: dict[str, Any]
    errors: tuple[ExecutionError, ...]
    status: HybridRuntimeStatus

    def to_dict(self) -> dict[str, Any]:
        """Serialize the runtime result into an API-friendly payload."""

        return {
            "request": self.request,
            "execution_plan": list(self.execution_plan),
            "executed_agents": list(self.executed_agents),
            "verified_results": dict(self.verified_results),
            "ai_results": dict(self.ai_results),
            "errors": [
                {
                    "agent_name": error.agent_name,
                    "message": error.message,
                    "exception_type": error.exception_type,
                }
                for error in self.errors
            ],
            "status": self.status.value,
        }
