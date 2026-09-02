"""API tests for canonical dataset ingestion."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.ingestion_routes import (
    get_dataset_ingestion_service,
    get_monthly_aggregation_service,
)
from src.database.base import Base
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.ingestion.service import (
    DatasetIngestionService,
)
from src.ingestion.aggregation import (
    MonthlyAggregationService,
)


def build_client() -> TestClient:
    engine = create_database_engine(
        DatabaseSettings(
            url=(
                "sqlite+pysqlite:///:memory:"
                "?check_same_thread=false"
            )
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
    aggregation_service = MonthlyAggregationService(
        unit_of_work_factory=lambda: PersistenceUnitOfWork(
            session_factory
        )
    )
    app = create_app()
    app.dependency_overrides[
        get_dataset_ingestion_service
    ] = lambda: service
    app.dependency_overrides[
        get_monthly_aggregation_service
    ] = lambda: aggregation_service
    return TestClient(app)


def request_payload() -> dict:
    return {
        "correlation_id": "INGEST-API-001",
        "company_code": "API-CO",
        "company_name": "API Company",
        "base_currency": "JOD",
        "source_name": "api-transactions.json",
        "source_format": "json",
        "records": [
            {
                "transaction_id": "API-TXN-001",
                "transaction_date": "2026-07-20",
                "accounting_period": "2026-07",
                "transaction_category": "OPERATING_EXPENSE",
                "description": "Monthly office rent",
                "amount": "2500.00",
                "currency": "JOD",
                "branch_code": "HQ",
                "branch_name": "Headquarters",
                "debit_account_code": "6100",
                "debit_account_name": "Rent Expense",
                "credit_account_code": "1100",
                "credit_account_name": "Cash",
            }
        ],
    }


def test_ingestion_endpoint_returns_auditable_batch_result():
    client = build_client()

    response = client.post(
        "/api/v1/ingestion/datasets",
        json=request_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["company_code"] == "API-CO"
    assert payload["accepted_rows"] == 1
    assert payload["rejected_rows"] == 0
    assert payload["branch_codes"] == ["HQ"]
    assert payload["batch_id"]

    stored_response = client.get(
        "/api/v1/ingestion/batches/"
        + payload["batch_id"]
    )

    assert stored_response.status_code == 200
    assert stored_response.json() == payload


def test_ingestion_endpoint_rejects_duplicate_correlation_id():
    client = build_client()
    payload = request_payload()

    first = client.post(
        "/api/v1/ingestion/datasets",
        json=payload,
    )
    second = client.post(
        "/api/v1/ingestion/datasets",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == (
        "DUPLICATE_INGESTION_CORRELATION_ID"
    )


def test_ingestion_batch_endpoint_returns_404():
    client = build_client()

    response = client.get(
        "/api/v1/ingestion/batches/unknown-batch"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == (
        "INGESTION_BATCH_NOT_FOUND"
    )


def test_monthly_summary_endpoint_returns_dashboard_contract():
    client = build_client()
    payload = request_payload()
    payload["records"][0][
        "debit_account_type"
    ] = "EXPENSE"
    payload["records"][0][
        "credit_account_type"
    ] = "ASSET"

    ingestion = client.post(
        "/api/v1/ingestion/datasets",
        json=payload,
    )
    batch_id = ingestion.json()["batch_id"]

    response = client.get(
        "/api/v1/ingestion/batches/"
        f"{batch_id}/monthly-summaries"
    )

    assert response.status_code == 200
    result = response.json()
    assert result["company_code"] == "API-CO"
    assert len(result["company_summaries"]) == 1
    assert result["company_summaries"][0][
        "totals"
    ]["expenses"] == "2500.00"
    assert result["data_profile"][
        "verified_capabilities"
    ] == []
