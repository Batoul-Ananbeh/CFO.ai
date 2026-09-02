"""Tests for deterministic JSON and CSV dataset ingestion."""

from __future__ import annotations

from sqlalchemy import select

from src.database.base import Base
from src.database.models import (
    Branch,
    Company,
    IngestionBatch,
    StagingRecord,
)
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.ingestion.models import (
    DatasetIngestionRequest,
)
from src.ingestion.service import (
    DatasetIngestionService,
)


def build_service():
    engine = create_database_engine(
        DatabaseSettings(
            url="sqlite+pysqlite:///:memory:"
        )
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(
        engine
    )
    service = DatasetIngestionService(
        unit_of_work_factory=lambda: PersistenceUnitOfWork(
            session_factory
        )
    )
    return engine, session_factory, service


def valid_row(
    *,
    transaction_id: str = "TXN-001",
    branch_code: str = "HQ",
    branch_name: str = "Headquarters",
) -> dict[str, str]:
    return {
        "transaction_id": transaction_id,
        "transaction_date": "2026-07-15",
        "accounting_period": "2026-07",
        "transaction_category": "SUPPLIER_INVOICE",
        "description": "Technology supplier invoice",
        "amount": "75000.00",
        "currency": "USD",
        "branch_code": branch_code,
        "branch_name": branch_name,
        "debit_account_code": "6200",
        "debit_account_name": "Technology Expense",
        "credit_account_code": "2100",
        "credit_account_name": "Accounts Payable",
    }


def test_json_ingestion_maps_company_branch_and_valid_row():
    engine, session_factory, service = build_service()

    response = service.ingest(
        DatasetIngestionRequest(
            correlation_id="INGEST-JSON-001",
            company_code="tech-co",
            company_name="Technology Company",
            base_currency="usd",
            source_name="transactions.json",
            source_format="json",
            records=[valid_row()],
        )
    )

    assert response.status == "COMPLETED"
    assert response.total_rows == 1
    assert response.accepted_rows == 1
    assert response.rejected_rows == 0
    assert response.branch_codes == ["HQ"]

    with session_factory() as session:
        company = session.scalar(
            select(Company)
        )
        branch = session.scalar(
            select(Branch)
        )
        record = session.scalar(
            select(StagingRecord)
        )

        assert company is not None
        assert company.code == "TECH-CO"
        assert branch is not None
        assert branch.company_id == company.id
        assert record is not None
        assert record.status == "VALIDATED"
        assert record.normalized_payload is not None
        assert record.normalized_payload[
            "amount"
        ] == "75000.00"

    engine.dispose()


def test_invalid_rows_are_retained_without_blocking_valid_rows():
    engine, session_factory, service = build_service()
    invalid = valid_row(
        transaction_id="TXN-BAD"
    )
    invalid["amount"] = "-1"

    response = service.ingest(
        DatasetIngestionRequest(
            correlation_id="INGEST-PARTIAL-001",
            company_code="MIXED-CO",
            company_name="Mixed Dataset Company",
            base_currency="JOD",
            source_name="mixed.json",
            source_format="json",
            records=[
                valid_row(),
                invalid,
            ],
        )
    )

    assert response.status == "PARTIAL"
    assert response.accepted_rows == 1
    assert response.rejected_rows == 1
    assert response.row_errors[0].transaction_id == (
        "TXN-BAD"
    )
    assert any(
        error["field"] == "amount"
        for error in response.row_errors[0].errors
    )

    with session_factory() as session:
        records = list(
            session.scalars(
                select(StagingRecord).order_by(
                    StagingRecord.source_row_number
                )
            )
        )
        batch = session.scalar(
            select(IngestionBatch)
        )

        assert [
            record.status
            for record in records
        ] == [
            "VALIDATED",
            "REJECTED",
        ]
        assert batch is not None
        assert batch.status == "PARTIAL"

    engine.dispose()


def test_csv_ingestion_uses_header_aware_row_numbers():
    engine, _, service = build_service()
    csv_content = (
        "transaction_id,transaction_date,accounting_period,"
        "transaction_category,description,amount,currency,"
        "branch_code,branch_name,debit_account_code,"
        "debit_account_name,credit_account_code,"
        "credit_account_name\n"
        "CSV-001,2026-07-15,2026-07,CASH_SALE,"
        "Cash sale,100.00,JOD,AMMAN,Amman Branch,"
        "1100,Cash,4100,Sales Revenue\n"
    )

    response = service.ingest(
        DatasetIngestionRequest(
            correlation_id="INGEST-CSV-001",
            company_code="RETAIL-CO",
            company_name="Retail Company",
            base_currency="JOD",
            source_name="transactions.csv",
            source_format="csv",
            csv_content=csv_content,
        )
    )

    assert response.status == "COMPLETED"
    assert response.accepted_rows == 1
    assert response.branch_codes == ["AMMAN"]

    engine.dispose()


def test_duplicate_transaction_in_one_dataset_is_rejected():
    engine, _, service = build_service()

    response = service.ingest(
        DatasetIngestionRequest(
            correlation_id="INGEST-DUPLICATE-TXN",
            company_code="DUP-TXN",
            company_name="Duplicate Transaction Company",
            base_currency="USD",
            source_name="duplicate.json",
            source_format="json",
            records=[
                valid_row(),
                valid_row(),
            ],
        )
    )

    assert response.status == "PARTIAL"
    assert response.accepted_rows == 1
    assert response.rejected_rows == 1
    assert response.row_errors[0].errors == [
        {
            "field": "transaction_id",
            "code": "DUPLICATE_IN_DATASET",
            "message": (
                "transaction_id must be unique within the dataset."
            ),
        }
    ]

    engine.dispose()
