"""Persisted analysis history API tests."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies import (
    get_database_session,
)
from src.database.base import Base
from src.database.models import (
    AgentExecutionRecord,
    AnalysisRecord,
    AuditLogRecord,
    Branch,
    Company,
)
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings


def build_history_client():
    """Create an isolated API and seeded history database."""

    settings = DatabaseSettings(
        url="sqlite+pysqlite:///:memory:",
        echo=False,
    )

    engine = create_database_engine(
        settings
    )

    Base.metadata.create_all(
        engine
    )

    session_factory = create_session_factory(
        engine
    )

    timestamp = datetime.now(
        timezone.utc
    )

    with session_factory() as session:
        company = Company(
            code="PHARMA-GROUP",
            name="Pharmacy Group",
            base_currency="JOD",
        )

        branch = Branch(
            company=company,
            code="MAIN",
            name="Main Branch",
        )

        analysis = AnalysisRecord(
            company=company,
            branch=branch,
            correlation_id="CORR-HISTORY-001",
            request_text="اشرح القيد المحاسبي",
            status="COMPLETED",
            financial_input={
                "transaction_id": "TXN-HISTORY-001",
            },
            metadata_payload={
                "source": "history-test",
            },
            execution_plan=[
                "general_ledger_ai",
            ],
            executed_agents=[
                "general_ledger_ai",
            ],
            verified_results={
                "status": "APPROVED",
            },
            ai_results={
                "general_ledger_ai": {
                    "summary": "Verified.",
                },
            },
            final_agent="general_ledger_ai",
            final_output={
                "summary": "Verified.",
            },
            errors=[],
            started_at=timestamp,
            completed_at=timestamp,
        )

        execution = AgentExecutionRecord(
            analysis=analysis,
            agent_name="general_ledger_ai",
            sequence_number=1,
            status="COMPLETED",
            input_payload={},
            output_payload={
                "summary": "Verified.",
            },
            prompt_tokens=1209,
            output_tokens=274,
            total_tokens=2604,
            thought_tokens=1121,
        )

        audit_log = AuditLogRecord(
            company=company,
            branch=branch,
            analysis=analysis,
            action="ANALYSIS_COMPLETED",
            entity_type="analysis",
            entity_id=analysis.id,
            actor_type="SYSTEM",
            details={
                "status": "COMPLETED",
            },
        )

        session.add_all(
            [
                company,
                analysis,
                execution,
                audit_log,
            ]
        )

        session.commit()

        analysis_id = analysis.id
        company_id = company.id

    app = create_app()

    def override_database_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[
        get_database_session
    ] = override_database_session

    client = TestClient(
        app
    )

    return (
        engine,
        client,
        analysis_id,
        company_id,
    )


def test_get_persisted_analysis():
    (
        engine,
        client,
        analysis_id,
        _,
    ) = build_history_client()

    response = client.get(
        f"/api/v1/analyses/{analysis_id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == analysis_id

    assert payload["correlation_id"] == (
        "CORR-HISTORY-001"
    )

    assert payload["company"]["code"] == (
        "PHARMA-GROUP"
    )

    assert payload["branch"]["code"] == "MAIN"

    assert payload["final_agent"] == (
        "general_ledger_ai"
    )

    assert len(
        payload["agent_executions"]
    ) == 1

    assert payload["agent_executions"][0][
        "total_tokens"
    ] == 2604

    assert len(payload["audit_logs"]) == 1

    engine.dispose()


def test_get_unknown_analysis_returns_404():
    engine, client, _, _ = (
        build_history_client()
    )

    response = client.get(
        "/api/v1/analyses/unknown-analysis"
    )

    assert response.status_code == 404

    engine.dispose()


def test_list_company_analyses_by_code():
    engine, client, analysis_id, _ = (
        build_history_client()
    )

    response = client.get(
        "/api/v1/companies/"
        "PHARMA-GROUP/analyses"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert payload["limit"] == 50
    assert payload["offset"] == 0

    assert payload["items"][0]["id"] == (
        analysis_id
    )

    engine.dispose()


def test_list_unknown_company_returns_404():
    engine, client, _, _ = (
        build_history_client()
    )

    response = client.get(
        "/api/v1/companies/"
        "UNKNOWN-COMPANY/analyses"
    )

    assert response.status_code == 404

    engine.dispose()