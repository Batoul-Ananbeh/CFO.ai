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
