"""Shared context passed between workflow stages."""

from typing import Any

from pydantic import Field

from src.schemas.common import StrictModel


class WorkflowContext(StrictModel):
    correlation_id: str = Field(min_length=1)

    data: dict[str, Any] = Field(default_factory=dict)

    metadata: dict[str, Any] = Field(default_factory=dict)

    completed_steps: list[str] = Field(default_factory=list)