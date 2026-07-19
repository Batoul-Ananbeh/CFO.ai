"""Schemas for the Financial Controller Agent."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from src.schemas.common import (
    AgentResultBase,
    EvidenceReference,
    Money,
    StrictModel,
)
from src.schemas.enums import (
    AgentName,
    ControllerDecisionStatus,
    ReportType,
    Severity,
    ValidationCheckStatus,
)


class ValidationCheck(StrictModel):
    """One validation rule executed by the Controller."""

    code: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ValidationCheckStatus
    details: str | None = None


class TrialBalanceInput(StrictModel):
    """Input required to validate a trial balance."""

    report_id: str = Field(min_length=1)
    accounting_period: str = Field(min_length=1)
    total_debit: Money
    total_credit: Money
    originating_agent: AgentName = AgentName.GENERAL_LEDGER
    evidence_references: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_same_currency(self) -> "TrialBalanceInput":
        if self.total_debit.currency != self.total_credit.currency:
            raise ValueError(
                "total_debit and total_credit must use the same currency"
            )

        return self


class ControllerIssue(StrictModel):
    """Issue detected by the Controller."""

    code: str = Field(min_length=1)
    severity: Severity
    description: str = Field(min_length=1)
    financial_difference: Money | None = None
    source_references: list[str] = Field(default_factory=list)


class ControllerResult(AgentResultBase):
    """Structured output returned by the Controller Agent."""

    review_id: str = Field(min_length=1)
    report_type: ReportType
    accounting_period: str = Field(min_length=1)
    decision_status: ControllerDecisionStatus

    checks: list[ValidationCheck] = Field(default_factory=list)
    issues: list[ControllerIssue] = Field(default_factory=list)

    total_debit: Money | None = None
    total_credit: Money | None = None
    balance_difference: Money | None = None

    severity: Severity = Severity.INFO
    requires_human_approval: bool = False


def calculate_balance_difference(
    total_debit: Decimal,
    total_credit: Decimal,
) -> Decimal:
    """Return the absolute difference between debit and credit totals."""

    return abs(total_debit - total_credit)