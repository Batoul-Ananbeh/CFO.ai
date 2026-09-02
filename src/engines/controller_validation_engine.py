"""Deterministic validation engine for the Financial Controller Agent."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.schemas.common import (
    ApprovalRequirement,
    Money,
    RequiredAction,
)
from src.schemas.controller import (
    ControllerIssue,
    ControllerResult,
    TrialBalanceInput,
    ValidationCheck,
    calculate_balance_difference,
)
from src.schemas.enums import (
    ControllerDecisionStatus,
    ReportType,
    Severity,
    ValidationCheckStatus,
)


def _new_review_id() -> str:
    """Generate a unique Controller review identifier."""

    return f"CTRL-{uuid4().hex[:12].upper()}"


def _severity_from_difference(
    difference: Decimal,
) -> Severity:
    """
    Return a temporary severity based on whether a difference exists.

    Materiality thresholds will later come from company configuration.
    """

    if difference == Decimal("0"):
        return Severity.INFO

    return Severity.HIGH


def validate_trial_balance(
    input_data: TrialBalanceInput,
    correlation_id: str,
) -> ControllerResult:
    """
    Validate that total debits equal total credits.

    This function is deterministic:
    - It performs no LLM calls.
    - It does not invent data.
    - It uses Decimal for all financial calculations.
    """

    difference = calculate_balance_difference(
        total_debit=input_data.total_debit.amount,
        total_credit=input_data.total_credit.amount,
    )

    currency = input_data.total_debit.currency

    checks: list[ValidationCheck] = []
    issues: list[ControllerIssue] = []
    required_actions: list[RequiredAction] = []

    if difference == Decimal("0"):
        checks.append(
            ValidationCheck(
                code="TRIAL_BALANCE_BALANCED",
                description="Total debits equal total credits.",
                status=ValidationCheckStatus.PASSED,
                details="The trial balance is balanced.",
            )
        )

        decision_status = ControllerDecisionStatus.APPROVED
        severity = Severity.INFO
        confidence_score = 1.0
        summary = (
            "The trial balance is balanced and can proceed "
            "to the next review stage."
        )

    else:
        checks.append(
            ValidationCheck(
                code="TRIAL_BALANCE_BALANCED",
                description="Total debits must equal total credits.",
                status=ValidationCheckStatus.FAILED,
                details=(
                    f"A balance difference of {difference} "
                    f"{currency} was detected."
                ),
            )
        )

        issues.append(
            ControllerIssue(
                code="UNBALANCED_TRIAL_BALANCE",
                severity=_severity_from_difference(difference),
                description=(
                    "The trial balance cannot be approved because "
                    "total debits do not equal total credits."
                ),
                financial_difference=Money(
                    amount=difference,
                    currency=currency,
                ),
                source_references=[input_data.report_id],
            )
        )

        required_actions.append(
            RequiredAction(
                assigned_to="general_ledger_agent",
                action=(
                    "Review the journal entries and resolve "
                    "the trial balance difference."
                ),
                requires_human_action=False,
            )
        )

        decision_status = (
            ControllerDecisionStatus.REQUIRES_CORRECTION
        )
        severity = Severity.HIGH
        confidence_score = 1.0
        summary = (
            "The trial balance cannot be approved until "
            f"the {difference} {currency} difference is resolved."
        )

    return ControllerResult(
        correlation_id=correlation_id,
        confidence_score=confidence_score,
        summary=summary,
        evidence_references=input_data.evidence_references,
        warnings=[],
        errors=[],
        required_actions=required_actions,
        approval=ApprovalRequirement(required=False),
        review_id=_new_review_id(),
        report_type=ReportType.TRIAL_BALANCE,
        accounting_period=input_data.accounting_period,
        decision_status=decision_status,
        checks=checks,
        issues=issues,
        total_debit=input_data.total_debit,
        total_credit=input_data.total_credit,
        balance_difference=Money(
            amount=difference,
            currency=currency,
        ),
        severity=severity,
        requires_human_approval=False,
    )


def validate_journal_entry_balance(
    input_data: TrialBalanceInput,
    correlation_id: str,
) -> ControllerResult:
    """Validate debit-credit equality for one draft journal entry."""

    difference = calculate_balance_difference(
        total_debit=input_data.total_debit.amount,
        total_credit=input_data.total_credit.amount,
    )
    currency = input_data.total_debit.currency
    checks: list[ValidationCheck] = []
    issues: list[ControllerIssue] = []
    required_actions: list[RequiredAction] = []

    if difference == Decimal("0"):
        checks.append(
            ValidationCheck(
                code="JOURNAL_ENTRY_BALANCED",
                description=(
                    "Journal-entry debits equal journal-entry credits."
                ),
                status=ValidationCheckStatus.PASSED,
                details="The draft journal entry is balanced.",
            )
        )
        decision_status = ControllerDecisionStatus.APPROVED
        severity = Severity.INFO
        summary = (
            "The draft journal entry passed the automated "
            "debit-credit equality check and can proceed to the "
            "next review stage."
        )
    else:
        checks.append(
            ValidationCheck(
                code="JOURNAL_ENTRY_BALANCED",
                description=(
                    "Journal-entry debits must equal journal-entry credits."
                ),
                status=ValidationCheckStatus.FAILED,
                details=(
                    f"A journal-entry difference of {difference} "
                    f"{currency} was detected."
                ),
            )
        )
        issues.append(
            ControllerIssue(
                code="UNBALANCED_JOURNAL_ENTRY",
                severity=_severity_from_difference(difference),
                description=(
                    "The draft journal entry cannot pass Controller "
                    "review because its debits and credits differ."
                ),
                financial_difference=Money(
                    amount=difference,
                    currency=currency,
                ),
                source_references=[input_data.report_id],
            )
        )
        required_actions.append(
            RequiredAction(
                assigned_to="general_ledger_agent",
                action=(
                    "Review the draft journal entry and resolve "
                    "its debit-credit difference."
                ),
                requires_human_action=False,
            )
        )
        decision_status = (
            ControllerDecisionStatus.REQUIRES_CORRECTION
        )
        severity = Severity.HIGH
        summary = (
            "The draft journal entry cannot pass Controller review "
            f"until the {difference} {currency} difference is resolved."
        )

    return ControllerResult(
        correlation_id=correlation_id,
        confidence_score=1.0,
        summary=summary,
        evidence_references=input_data.evidence_references,
        warnings=[],
        errors=[],
        required_actions=required_actions,
        approval=ApprovalRequirement(required=False),
        review_id=_new_review_id(),
        report_type=ReportType.JOURNAL_ENTRY,
        accounting_period=input_data.accounting_period,
        decision_status=decision_status,
        checks=checks,
        issues=issues,
        total_debit=input_data.total_debit,
        total_credit=input_data.total_credit,
        balance_difference=Money(
            amount=difference,
            currency=currency,
        ),
        severity=severity,
        requires_human_approval=False,
    )
