"""Tests for the General Ledger Engine."""

from decimal import Decimal

from src.engines.general_ledger_engine import (
    prepare_draft_journal_entry,
)
from src.schemas.common import Money
from src.schemas.enums import (
    JournalLineType,
    LedgerDecisionStatus,
    Severity,
    TransactionCategory,
)
from src.schemas.general_ledger import (
    LedgerAccount,
    LedgerTransactionInput,
)


def test_engine_prepares_balanced_cash_sale_entry() -> None:
    input_data = LedgerTransactionInput(
        transaction_id="TXN-GL-001",
        accounting_period="2026-07",
        transaction_category=TransactionCategory.CASH_SALE,
        description="Cash sale",
        amount=Money(
            amount=Decimal("1000"),
            currency="USD",
        ),
        debit_account=LedgerAccount(
            account_code="1100",
            account_name="Bank",
        ),
        credit_account=LedgerAccount(
            account_code="4100",
            account_name="Sales Revenue",
        ),
    )

    result = prepare_draft_journal_entry(
        input_data=input_data,
        correlation_id="CORR-GL-001",
    )

    assert (
        result.decision_status
        == LedgerDecisionStatus.READY_FOR_CONTROLLER_REVIEW
    )
    assert result.severity == Severity.INFO
    assert result.journal_entry is not None

    journal = result.journal_entry

    assert len(journal.lines) == 2
    assert journal.total_debit.amount == Decimal("1000")
    assert journal.total_credit.amount == Decimal("1000")
    assert journal.balance_difference.amount == Decimal("0")

    assert journal.lines[0].line_type == JournalLineType.DEBIT
    assert journal.lines[0].debit.amount == Decimal("1000")
    assert journal.lines[0].credit.amount == Decimal("0")

    assert journal.lines[1].line_type == JournalLineType.CREDIT
    assert journal.lines[1].debit.amount == Decimal("0")
    assert journal.lines[1].credit.amount == Decimal("1000")


def test_engine_preserves_currency() -> None:
    input_data = LedgerTransactionInput(
        transaction_id="TXN-GL-002",
        accounting_period="2026-07",
        transaction_category=TransactionCategory.SUPPLIER_INVOICE,
        description="Supplier invoice",
        amount=Money(
            amount=Decimal("500.125"),
            currency="JOD",
        ),
        debit_account=LedgerAccount(
            account_code="6100",
            account_name="Operating Expense",
        ),
        credit_account=LedgerAccount(
            account_code="2100",
            account_name="Accounts Payable",
        ),
    )

    result = prepare_draft_journal_entry(
        input_data=input_data,
        correlation_id="CORR-GL-002",
    )

    assert result.journal_entry is not None
    assert result.journal_entry.total_debit.currency == "JOD"
    assert result.journal_entry.total_credit.currency == "JOD"
    assert (
        result.journal_entry.balance_difference.currency
        == "JOD"
    )