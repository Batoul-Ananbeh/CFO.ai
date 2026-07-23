"""Result models for the unified CFO runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.ai.context_utils import to_json_compatible
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
        """
        Serialize the complete runtime result.

        Converts Pydantic models, Decimal values, enums, tuples,
        and nested financial objects into JSON-compatible values.
        """

        payload = {
            "request": self.request,
            "execution_plan": list(
                self.execution_plan
            ),
            "executed_agents": list(
                self.executed_agents
            ),
            "verified_results": (
                self.verified_results
            ),
            "ai_results": self.ai_results,
            "errors": [
                {
                    "agent_name": error.agent_name,
                    "message": error.message,
                    "exception_type": (
                        error.exception_type
                    ),
                    "category": error.category.value,
                    "provider_status_code": (
                        error.provider_status_code
                    ),
                    "retryable": error.retryable,
                }
                for error in self.errors
            ],
            "status": self.status.value,
        }

        serialized_payload = to_json_compatible(
            payload
        )

        if not isinstance(
            serialized_payload,
            dict,
        ):
            raise TypeError(
                "Runtime serialization must produce a dictionary."
            )

        return serialized_payload