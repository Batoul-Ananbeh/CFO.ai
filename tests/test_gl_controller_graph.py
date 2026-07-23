"""Integration tests for the General Ledger to Controller LangGraph."""

from decimal import Decimal

from src.graphs.builder import build_gl_controller_graph
from src.schemas.common import Money
from src.schemas.enums import TransactionCategory
from src.schemas.general_ledger import (
    LedgerAccount,
    LedgerTransactionInput,
)


def test_gl_controller_graph_runs_successfully() -> None:
    graph = build_gl_controller_graph()

    input_data = LedgerTransactionInput(
        transaction_id="TXN-GRAPH-001",
        accounting_period="2026-07",
        transaction_category=TransactionCategory.CASH_SALE,
        description="Cash sale processed through LangGraph",
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

    result = graph.invoke(
        {
            "correlation_id": "CORR-GRAPH-001",
            "input_data": input_data,
            "metadata": {
                "source": "pytest",
            },
            "current_step": "start",
            "completed_steps": [],
            "errors": [],
        }
    )

    assert result["general_ledger_result"] is not None
    assert result["general_ledger_result"].journal_entry is not None

    assert result["controller_result"] is not None

    assert result["current_step"] == "approved"

    assert result["completed_steps"] == [
        "general_ledger",
        "controller",
    ]

    assert result["final_status"]


    assert result["final_status"] == "APPROVED"
    assert result["summary"] == (
        "The financial entry passed the automated Controller checks. "
        "This does not authorize posting or payment."
    )
