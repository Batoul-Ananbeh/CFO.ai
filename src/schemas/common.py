"""Common schemas shared across CFO.ai agents."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from src.schemas.currency import normalize_currency_code


class StrictModel(BaseModel):
    """Base schema that rejects unknown fields."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class Money(StrictModel):
    """Precise monetary amount using an ISO 4217 currency code."""

    amount: Decimal
    currency: str

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        return normalize_currency_code(value)

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> str:
        return format(value, "f")


class EvidenceReference(StrictModel):
    """Reference to source evidence used by an Agent or Engine."""

    reference_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_location: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WarningItem(StrictModel):
    """Non-blocking warning returned by an Agent or Engine."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorItem(StrictModel):
    """Blocking or processing error."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class RequiredAction(StrictModel):
    """Action assigned to an Agent or human reviewer."""

    assigned_to: str = Field(min_length=1)
    action: str = Field(min_length=1)
    due_date: str | None = None
    requires_human_action: bool = False


class ApprovalRequirement(StrictModel):
    """Human approval requirement for sensitive financial actions."""

    required: bool = False
    approver_role: str | None = None
    reason: str | None = None
    approval_reference: str | None = None


class AgentResultBase(StrictModel):
    """Base fields shared by all Agent outputs."""

    correlation_id: str = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)

    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)
    errors: list[ErrorItem] = Field(default_factory=list)
    required_actions: list[RequiredAction] = Field(default_factory=list)

    approval: ApprovalRequirement = Field(
        default_factory=ApprovalRequirement
    )