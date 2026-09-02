"""API models for persisted CFO analysis history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class CompanyReference(BaseModel):
    """Lightweight company information."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    code: str
    name: str
    base_currency: str


class BranchReference(BaseModel):
    """Lightweight branch information."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    code: str
    name: str


class AgentExecutionHistory(BaseModel):
    """Persisted execution details for one CFO agent."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    agent_name: str
    sequence_number: int
    status: str

    input_payload: dict[str, Any] = Field(
        default_factory=dict,
    )

    output_payload: dict[str, Any] | None = None

    error_category: str | None = None
    error_message: str | None = None

    provider_status_code: int | None = None
    retryable: bool = False

    prompt_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    thought_tokens: int | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class AuditLogHistory(BaseModel):
    """Persisted audit event details."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    action: str
    entity_type: str
    entity_id: str | None = None
    actor_type: str
    actor_id: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime


class AnalysisHistorySummary(BaseModel):
    """Summary of one persisted CFO analysis."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    correlation_id: str
    request: str
    status: str

    company: CompanyReference
    branch: BranchReference | None = None

    final_agent: str | None = None

    created_at: datetime
    completed_at: datetime | None = None


class AnalysisHistoryDetail(
    AnalysisHistorySummary
):
    """Complete persisted CFO analysis details."""

    financial_input: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    execution_plan: list[str] = Field(
        default_factory=list,
    )

    executed_agents: list[str] = Field(
        default_factory=list,
    )

    verified_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    ai_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    final_output: dict[str, Any] | None = None

    errors: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    started_at: datetime | None = None

    agent_executions: list[
        AgentExecutionHistory
    ] = Field(
        default_factory=list,
    )

    audit_logs: list[AuditLogHistory] = Field(
        default_factory=list,
    )


class AnalysisHistoryList(BaseModel):
    """Paginated company analysis history."""

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[AnalysisHistorySummary] = Field(
        default_factory=list,
    )

    total: int
    limit: int
    offset: int