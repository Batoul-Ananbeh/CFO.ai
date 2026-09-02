"""Tests for the General Ledger to Controller workflow."""

from decimal import Decimal

from src.schemas.common import Money
from src.schemas.enums import ReportType, TransactionCategory
from src.schemas.general_ledger import (
    LedgerAccount,
    LedgerTransactionInput,
)
from src.workflows.gl_controller_workflow import GLControllerWorkflow


def test_gl_controller_workflow_runs_through_langgraph() -> None:
    workflow = GLControllerWorkflow()

    input_data = LedgerTransactionInput(
        transaction_id="TXN-WORKFLOW-001",
        accounting_period="2026-07",
        transaction_category=TransactionCategory.CASH_SALE,
        description="Cash sale processed through the workflow",
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

    result = workflow.run(
        input_data=input_data,
        correlation_id="CORR-WORKFLOW-001",
    )

    assert result.correlation_id == "CORR-WORKFLOW-001"
    assert result.general_ledger_result is not None
    assert result.general_ledger_result.journal_entry is not None
    assert result.controller_result is not None
    assert result.controller_result.report_type == (
        ReportType.JOURNAL_ENTRY
    )
    assert result.controller_result.checks[0].code == (
        "JOURNAL_ENTRY_BALANCED"
    )
    assert result.final_status == "APPROVED"
    assert result.summary == (
        "The financial entry passed the automated Controller checks. "
        "This does not authorize posting or payment."
    )
