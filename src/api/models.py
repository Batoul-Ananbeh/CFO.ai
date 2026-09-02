"""Public API models for CFO.ai."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health information returned by the CFO.ai API."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    api_version: str


class AgentDescriptor(BaseModel):
    """Describe one AI agent exposed by the API."""

    model_config = ConfigDict(extra="forbid")

    name: str
    dependencies: list[str] = Field(
        default_factory=list,
    )


class AgentCatalogResponse(BaseModel):
    """Catalog of dynamically selectable CFO agents."""

    model_config = ConfigDict(extra="forbid")

    agents: list[AgentDescriptor]
    total: int


class APIConflictResponse(BaseModel):
    """Public response for a duplicate idempotency key."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["DUPLICATE_CORRELATION_ID"]
    message: str
    correlation_id: str


class ReadinessComponent(BaseModel):
    """Readiness state for one external or internal component."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]
    detail: str


class ReadinessResponse(BaseModel):
    """Operational readiness of the CFO.ai service."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]
    service: str
    components: dict[str, ReadinessComponent]
