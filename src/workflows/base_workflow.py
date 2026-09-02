"""Base workflow utilities for CFO.ai."""

from abc import ABC
from typing import Any

from src.schemas.workflows import WorkflowResultBase


class BaseWorkflow(ABC):
    """Shared behavior for CFO.ai workflows."""

    @staticmethod
    def require_result(
        value: Any,
        error_message: str,
    ) -> Any:
        if value is None:
            raise ValueError(error_message)

        return value

    @staticmethod
    def normalize_status(status: Any) -> str:
        value = getattr(status, "value", status)
        return str(value)

    @staticmethod
    def validate_correlation_id(correlation_id: str) -> str:
        normalized_id = correlation_id.strip()

        if not normalized_id:
            raise ValueError("correlation_id must not be empty.")

        return normalized_id

    @staticmethod
    def validate_workflow_result(
        result: WorkflowResultBase,
    ) -> WorkflowResultBase:
        if not result.final_status.strip():
            raise ValueError("Workflow final_status must not be empty.")

        return result