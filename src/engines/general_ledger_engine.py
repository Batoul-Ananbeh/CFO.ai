"""Deterministic engine for preparing draft journal entries."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.schemas.common import (
    ApprovalRequirement,
    Money,
    RequiredAction,
)
from src.schemas.enums import (
    JournalLineType,
    LedgerDecisionStatus,
    Severity,
)
from src.schemas.general_ledger import (
    DraftJournalEntry,
    GeneralLedgerResult,
    JournalLine,
    LedgerTransactionInput,
)


def _new_processing_id() -> str:
    """Generate a unique GL processing identifier."""

    return f"GL-{uuid4().hex[:12].upper()}"


def _new_journal_id() -> str:
    """Generate a unique draft journal identifier."""

    return f"JRN-DRAFT-{uuid4().hex[:12].upper()}"


def prepare_draft_journal_entry(
    input_data: LedgerTransactionInput,
    correlation_id: str,
) -> GeneralLedgerResult:
    """
    Prepare a balanced draft journal entry from a verified business event.

    This function is deterministic:
    - It performs no LLM calls.
    - It uses Decimal for money.
    - It does not post the entry.
    - It does not approve its own output.
    """

    amount = input_data.amount.amount
    currency = input_data.amount.currency
    zero = Decimal("0")

    debit_line = JournalLine(
        line_number=1,
        line_type=JournalLineType.DEBIT,
        account_code=input_data.debit_account.account_code,
        account_name=input_data.debit_account.account_name,
        debit=Money(
            amount=amount,
            currency=currency,
        ),
        credit=Money(
            amount=zero,
            currency=currency,
        ),
    )

    credit_line = JournalLine(
        line_number=2,
        line_type=JournalLineType.CREDIT,
        account_code=input_data.credit_account.account_code,
        account_name=input_data.credit_account.account_name,
        debit=Money(
            amount=zero,
            currency=currency,
        ),
        credit=Money(
            amount=amount,
            currency=currency,
        ),
    )

    total_debit = amount
    total_credit = amount
    balance_difference = abs(total_debit - total_credit)

    journal_entry = DraftJournalEntry(
        journal_id=_new_journal_id(),
        transaction_id=input_data.transaction_id,
        accounting_period=input_data.accounting_period,
        description=input_data.description,
        lines=[
            debit_line,
            credit_line,
        ],
        total_debit=Money(
            amount=total_debit,
            currency=currency,
        ),
        total_credit=Money(
            amount=total_credit,
            currency=currency,
        ),
        balance_difference=Money(
            amount=balance_difference,
            currency=currency,
        ),
    )

    return GeneralLedgerResult(
        correlation_id=correlation_id,
        confidence_score=1.0,
        summary=(
            "A balanced draft journal entry was prepared and is ready "
            "for Financial Controller review."
        ),
        evidence_references=input_data.evidence_references,
        warnings=[],
        errors=[],
        required_actions=[
            RequiredAction(
                assigned_to="financial_controller_agent",
                action=(
                    "Review and approve the draft journal entry."
                ),
                requires_human_action=False,
            )
        ],
        approval=ApprovalRequirement(required=False),
        processing_id=_new_processing_id(),
        transaction_id=input_data.transaction_id,
        accounting_period=input_data.accounting_period,
        transaction_category=input_data.transaction_category,
        decision_status=(
            LedgerDecisionStatus.READY_FOR_CONTROLLER_REVIEW
        ),
        severity=Severity.INFO,
        journal_entry=journal_entry,
        requires_human_approval=False,
    )