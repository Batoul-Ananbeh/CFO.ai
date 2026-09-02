"""Tests for deterministic, currency-safe monthly aggregation."""

from __future__ import annotations

from decimal import Decimal

from src.database.base import Base
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.ingestion.aggregation import (
    MonthlyAggregationService,
)
from src.ingestion.models import (
    DatasetIngestionRequest,
)
from src.ingestion.service import (
    DatasetIngestionService,
)


def build_services():
    engine = create_database_engine(
        DatabaseSettings(
            url="sqlite+pysqlite:///:memory:"
        )
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(
        engine
    )
    factory = lambda: PersistenceUnitOfWork(
        session_factory
    )
    return (
        engine,
        DatasetIngestionService(
            unit_of_work_factory=factory
        ),
        MonthlyAggregationService(
            unit_of_work_factory=factory
        ),
    )


def typed_row(
    *,
    transaction_id: str,
    transaction_date: str,
    accounting_period: str,
    amount: str,
    category: str,
    branch_code: str = "HQ",
    currency: str = "USD",
    debit_type: str = "ASSET",
    credit_type: str = "REVENUE",
) -> dict[str, str]:
    return {
        "transaction_id": transaction_id,
        "transaction_date": transaction_date,
        "accounting_period": accounting_period,
        "transaction_category": category,
        "description": f"Transaction {transaction_id}",
        "amount": amount,
        "currency": currency,
        "branch_code": branch_code,
        "branch_name": f"{branch_code} Branch",
        "debit_account_code": "D-100",
        "debit_account_name": "Debit Account",
        "debit_account_type": debit_type,
        "credit_account_code": "C-100",
        "credit_account_name": "Credit Account",
        "credit_account_type": credit_type,
    }


def complete_request() -> DatasetIngestionRequest:
    return DatasetIngestionRequest(
        correlation_id="AGG-COMPLETE-001",
        company_code="AGG-CO",
        company_name="Aggregation Company",
        base_currency="USD",
        source_name="complete.json",
        source_format="json",
        dataset_scope="company_complete",
        expected_branch_codes=[
            "HQ",
            "BR-02",
        ],
        reporting_period_start="2026-01",
        reporting_period_end="2026-03",
        records=[
            typed_row(
                transaction_id="JAN-SALE",
                transaction_date="2026-01-10",
                accounting_period="2026-01",
                amount="100.00",
                category="CASH_SALE",
            ),
            typed_row(
                transaction_id="JAN-EXPENSE",
                transaction_date="2026-01-15",
                accounting_period="2026-01",
                amount="30.00",
                category="OPERATING_EXPENSE",
                debit_type="EXPENSE",
                credit_type="ASSET",
            ),
            typed_row(
                transaction_id="FEB-INVOICE",
                transaction_date="2026-02-12",
                accounting_period="2026-02",
                amount="50.00",
                category="SUPPLIER_INVOICE",
                branch_code="BR-02",
                debit_type="EXPENSE",
                credit_type="LIABILITY",
            ),
            typed_row(
                transaction_id="MAR-CAPITAL",
                transaction_date="2026-03-05",
                accounting_period="2026-03",
                amount="200.00",
                category="OWNER_CAPITAL",
                branch_code="BR-02",
                debit_type="ASSET",
                credit_type="EQUITY",
            ),
        ],
    )


def test_complete_company_dataset_unlocks_verified_capabilities():
    engine, ingestion, aggregation = build_services()
    batch = ingestion.ingest(
        complete_request()
    )

    result = aggregation.aggregate(
        batch.batch_id
    )

    assert result.data_profile.validation_status == "VERIFIED"
    assert result.data_profile.periods == [
        "2026-01",
        "2026-02",
        "2026-03",
    ]
    assert result.data_profile.classification_coverage == 1
    assert result.data_profile.verified_capabilities == [
        "multi_period_financial_history",
        "company_level_financial_context",
    ]

    january = result.company_summaries[0]
    assert january.accounting_period == "2026-01"
    assert january.totals.revenue == Decimal("100.00")
    assert january.totals.expenses == Decimal("30.00")
    assert january.totals.net_income == Decimal("70.00")
    assert january.totals.asset_change == Decimal("70.00")

    engine.dispose()


def test_branch_summaries_preserve_branch_provenance():
    engine, ingestion, aggregation = build_services()
    batch = ingestion.ingest(
        complete_request()
    )

    result = aggregation.aggregate(
        batch.batch_id
    )

    assert {
        summary.branch_code
        for summary in result.branch_summaries
    } == {
        "HQ",
        "BR-02",
    }
    february_branch = next(
        summary
        for summary in result.branch_summaries
        if summary.accounting_period == "2026-02"
    )
    assert february_branch.branch_code == "BR-02"
    assert february_branch.totals.expenses == Decimal("50.00")
    assert february_branch.totals.liability_change == Decimal("50.00")

    engine.dispose()


def test_aggregation_never_combines_currencies():
    engine, ingestion, aggregation = build_services()
    request = complete_request()
    request.records = [
        typed_row(
            transaction_id="USD-SALE",
            transaction_date="2026-01-10",
            accounting_period="2026-01",
            amount="100.00",
            category="CASH_SALE",
            currency="USD",
        ),
        typed_row(
            transaction_id="JOD-SALE",
            transaction_date="2026-01-11",
            accounting_period="2026-01",
            amount="70.00",
            category="CASH_SALE",
            currency="JOD",
        ),
    ]
    request.dataset_scope = "transaction_sample"
    request.expected_branch_codes = []
    request.reporting_period_start = None
    request.reporting_period_end = None

    batch = ingestion.ingest(request)
    result = aggregation.aggregate(
        batch.batch_id
    )

    assert len(result.company_summaries) == 2
    amounts = {
        summary.currency: summary.totals.revenue
        for summary in result.company_summaries
    }
    assert amounts == {
        "JOD": Decimal("70.00"),
        "USD": Decimal("100.00"),
    }

    engine.dispose()


def test_unclassified_rows_are_visible_but_do_not_unlock_ai():
    engine, ingestion, aggregation = build_services()
    row = typed_row(
        transaction_id="UNTYPED-001",
        transaction_date="2026-01-10",
        accounting_period="2026-01",
        amount="100.00",
        category="CASH_SALE",
    )
    row.pop("debit_account_type")
    row.pop("credit_account_type")

    request = DatasetIngestionRequest(
        correlation_id="AGG-UNTYPED-001",
        company_code="UNTYPED-CO",
        company_name="Untyped Company",
        base_currency="USD",
        source_name="untyped.json",
        source_format="json",
        records=[row],
    )
    batch = ingestion.ingest(request)
    result = aggregation.aggregate(
        batch.batch_id
    )

    summary = result.company_summaries[0]
    assert summary.total_transactions == 1
    assert summary.classified_transactions == 0
    assert summary.classification_coverage == 0
    assert summary.totals.revenue == Decimal("0")
    assert result.data_profile.verified_capabilities == []
    assert any(
        "lack account-type classification"
        in limitation
        for limitation in result.data_profile.limitations
    )

    engine.dispose()
