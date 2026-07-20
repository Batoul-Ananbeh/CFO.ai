"""Schemas for the General Ledger Agent."""

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
    JournalLineType,
    LedgerDecisionStatus,
    Severity,
    TransactionCategory,
)


class LedgerAccount(StrictModel):
    """A ledger account selected for a journal line."""

    account_code: str = Field(min_length=1)
    account_name: str = Field(min_length=1)


class LedgerTransactionInput(StrictModel):
    """Verified business event provided to the GL Agent."""

    transaction_id: str = Field(min_length=1)
    accounting_period: str = Field(min_length=1)
    transaction_category: TransactionCategory
    description: str = Field(min_length=1)

    amount: Money

    debit_account: LedgerAccount
    credit_account: LedgerAccount

    originating_agent: AgentName = AgentName.FINANCE_OPERATIONS
    evidence_references: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_accounts_and_amount(self) -> "LedgerTransactionInput":
        if self.amount.amount <= Decimal("0"):
            raise ValueError("transaction amount must be greater than zero")

        if (
            self.debit_account.account_code
            == self.credit_account.account_code
        ):
            raise ValueError(
                "debit and credit accounts must be different"
            )

        return self


class JournalLine(StrictModel):
    """One debit or credit line inside a draft journal entry."""

    line_number: int = Field(ge=1)
    line_type: JournalLineType

    account_code: str = Field(min_length=1)
    account_name: str = Field(min_length=1)

    debit: Money
    credit: Money

    @model_validator(mode="after")
    def validate_line(self) -> "JournalLine":
        if self.debit.currency != self.credit.currency:
            raise ValueError(
                "debit and credit currencies must match"
            )

        debit_amount = self.debit.amount
        credit_amount = self.credit.amount

        if debit_amount < Decimal("0") or credit_amount < Decimal("0"):
            raise ValueError(
                "journal line amounts cannot be negative"
            )

        if debit_amount > Decimal("0") and credit_amount > Decimal("0"):
            raise ValueError(
                "a journal line cannot contain both debit and credit"
            )

        if debit_amount == Decimal("0") and credit_amount == Decimal("0"):
            raise ValueError(
                "a journal line must contain a debit or credit amount"
            )

        if (
            self.line_type == JournalLineType.DEBIT
            and debit_amount == Decimal("0")
        ):
            raise ValueError(
                "DEBIT line must contain a debit amount"
            )

        if (
            self.line_type == JournalLineType.CREDIT
            and credit_amount == Decimal("0")
        ):
            raise ValueError(
                "CREDIT line must contain a credit amount"
            )

        return self


class DraftJournalEntry(StrictModel):
    """Balanced journal entry prepared for Controller review."""

    journal_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    accounting_period: str = Field(min_length=1)
    description: str = Field(min_length=1)

    lines: list[JournalLine] = Field(min_length=2)

    total_debit: Money
    total_credit: Money
    balance_difference: Money

    @model_validator(mode="after")
    def validate_currency_consistency(self) -> "DraftJournalEntry":
        currencies = {
            self.total_debit.currency,
            self.total_credit.currency,
            self.balance_difference.currency,
        }

        for line in self.lines:
            currencies.add(line.debit.currency)
            currencies.add(line.credit.currency)

        if len(currencies) != 1:
            raise ValueError(
                "all journal amounts must use the same currency"
            )

        return self


class GeneralLedgerResult(AgentResultBase):
    """Structured output returned by the GL Agent."""

    processing_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    accounting_period: str = Field(min_length=1)

    transaction_category: TransactionCategory
    decision_status: LedgerDecisionStatus
    severity: Severity

    journal_entry: DraftJournalEntry | None = None
    requires_human_approval: bool = False