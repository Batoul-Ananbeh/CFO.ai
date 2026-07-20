"""Tests for the General Ledger Agent."""

from decimal import Decimal

from src.agents.general_ledger_agent import GeneralLedgerAgent
from src.schemas.common import Money
from src.schemas.enums import (
    LedgerDecisionStatus,
    TransactionCategory,
)
from src.schemas.general_ledger import (
    LedgerAccount,
    LedgerTransactionInput,
)


def test_gl_agent_prepares_cash_sale_entry() -> None:
    agent = GeneralLedgerAgent()

    input_data = LedgerTransactionInput(
        transaction_id="TXN-AGENT-GL-001",
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

    result = agent.prepare_entry(
        input_data=input_data,
        correlation_id="CORR-AGENT-GL-001",
    )

    assert (
        result.decision_status
        == LedgerDecisionStatus.READY_FOR_CONTROLLER_REVIEW
    )
    assert result.journal_entry is not None
    assert result.journal_entry.balance_difference.amount == Decimal("0")


def test_gl_agent_preserves_transaction_data() -> None:
    agent = GeneralLedgerAgent()

    input_data = LedgerTransactionInput(
        transaction_id="TXN-AGENT-GL-002",
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

    result = agent.prepare_entry(
        input_data=input_data,
        correlation_id="CORR-AGENT-GL-002",
    )

    assert result.transaction_id == "TXN-AGENT-GL-002"
    assert result.accounting_period == "2026-07"
    assert result.journal_entry is not None
    assert result.journal_entry.total_debit.amount == Decimal("500.125")
    assert result.journal_entry.total_debit.currency == "JOD"


def test_gl_agent_explains_result() -> None:
    agent = GeneralLedgerAgent()

    input_data = LedgerTransactionInput(
        transaction_id="TXN-AGENT-GL-003",
        accounting_period="2026-07",
        transaction_category=TransactionCategory.CASH_SALE,
        description="Cash sale",
        amount=Money(
            amount=Decimal("750"),
            currency="EUR",
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

    result = agent.prepare_entry(
        input_data=input_data,
        correlation_id="CORR-AGENT-GL-003",
    )

    explanation = agent.explain(result)

    assert "750" in explanation
    assert "EUR" in explanation
    assert "Bank" in explanation
    assert "Sales Revenue" in explanation
    assert "جاهز" in explanation