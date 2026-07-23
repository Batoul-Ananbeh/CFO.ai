"""Tests for persistent company CFO reports from monthly summaries."""

from __future__ import annotations

from typing import Any, TypeVar

from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import select

from src.ai.errors import AIProviderError
from src.ai.models import AIRequest, AITextResult
from src.ai.outputs import (
    ChiefCFOBrief,
    ForecastAnalysis,
    RiskAssessment,
    StrategyAnalysis,
)
from src.ai.provider import LLMProvider
from src.api.app import create_app
from src.api.ingestion_routes import (
    get_company_cfo_report_service,
)
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.database.base import Base
from src.database.models import AnalysisRecord
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
from src.ingestion.company_report import (
    CompanyCFOReportRequest,
    CompanyCFOReportService,
)
from src.ingestion.models import (
    DatasetIngestionRequest,
)
from src.ingestion.service import (
    DatasetIngestionService,
)
from tests.test_monthly_financial_aggregation import (
    complete_request,
    typed_row,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class CompanyReportProvider(LLMProvider):
    """Return auditable structured outputs without network calls."""

    def __init__(
        self,
        *,
        fail_first: bool = False,
    ) -> None:
        self.requests: list[AIRequest] = []
        self.fail_first = fail_first

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        raise AssertionError("Text generation is not used.")

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        if self.fail_first:
            raise AIProviderError(
                "Provider rate limit.",
                provider="fake",
                status_code=429,
                retryable=True,
            )

        payloads: dict[type[BaseModel], dict[str, Any]] = {
            RiskAssessment: {
                "summary": "Verified company risk review.",
                "risk_level": "MEDIUM",
                "risk_findings": [],
                "missing_information": [],
                "recommended_controls": [],
            },
            ForecastAnalysis: {
                "summary": "Verified multi-period forecast.",
                "assumptions": [],
                "expected_scenario": [],
                "downside_risks": [],
                "recommendations": [],
            },
            StrategyAnalysis: {
                "summary": "Verified company strategy.",
                "strategic_priorities": [],
                "recommended_actions": [],
                "expected_benefits": [],
                "risks_and_tradeoffs": [],
            },
            ChiefCFOBrief: {
                "executive_summary": "Verified company CFO brief.",
                "key_financial_signals": [],
                "critical_risks": [],
                "recommended_decisions": [],
                "human_approvals_required": [],
            },
        }
        return output_schema.model_validate(
            payloads[output_schema]
        )


def build_report_system(
    provider: LLMProvider,
):
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
    ingestion = DatasetIngestionService(
        unit_of_work_factory=factory
    )
    aggregation = MonthlyAggregationService(
        unit_of_work_factory=factory
    )
    persistence = AnalysisPersistenceService(
        unit_of_work_factory=factory
    )
    report = CompanyCFOReportService(
        aggregation=aggregation,
        provider=provider,
        persistence=persistence,
    )
    return (
        engine,
        session_factory,
        ingestion,
        report,
    )


def test_complete_dataset_runs_four_agents_and_persists_report():
    provider = CompanyReportProvider()
    (
        engine,
        session_factory,
        ingestion,
        report,
    ) = build_report_system(provider)
    batch = ingestion.ingest(
        complete_request()
    )

    response = report.generate(
        batch_id=batch.batch_id,
        report_request=CompanyCFOReportRequest(
            correlation_id="COMPANY-REPORT-001"
        ),
    )

    assert response.status == "COMPLETED"
    assert response.executed_agents == [
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
        "chief_cfo_ai",
    ]
    assert response.final_agent == "chief_cfo_ai"
    assert response.analysis_id is not None
    assert len(provider.requests) == 4

    with session_factory() as session:
        stored = session.scalar(
            select(AnalysisRecord).where(
                AnalysisRecord.id
                == response.analysis_id
            )
        )
        assert stored is not None
        assert stored.metadata_payload[
            "batch_id"
        ] == batch.batch_id
        assert stored.final_agent == "chief_cfo_ai"

    engine.dispose()


def test_incomplete_dataset_returns_deterministic_limit_without_ai():
    provider = CompanyReportProvider()
    engine, _, ingestion, report = build_report_system(
        provider
    )
    request = DatasetIngestionRequest(
        correlation_id="SAMPLE-BATCH-001",
        company_code="SAMPLE-CO",
        company_name="Sample Company",
        base_currency="USD",
        source_name="sample.json",
        source_format="json",
        records=[
            typed_row(
                transaction_id="SAMPLE-TXN-001",
                transaction_date="2026-01-10",
                accounting_period="2026-01",
                amount="100.00",
                category="CASH_SALE",
            )
        ],
    )
    batch = ingestion.ingest(request)

    response = report.generate(
        batch_id=batch.batch_id,
        report_request=CompanyCFOReportRequest(
            correlation_id="COMPANY-REPORT-LIMITED"
        ),
    )

    assert response.status == "COMPLETED"
    assert response.execution_plan == []
    assert response.executed_agents == []
    assert response.final_agent == (
        "deterministic_aggregation"
    )
    assert response.final_output is not None
    assert response.final_output[
        "report_status"
    ] == "INSUFFICIENT_DATA"
    assert provider.requests == []
    assert response.analysis_id is not None

    engine.dispose()


def test_provider_failure_stops_without_dependency_error_cascade():
    provider = CompanyReportProvider(
        fail_first=True
    )
    engine, _, ingestion, report = build_report_system(
        provider
    )
    batch = ingestion.ingest(
        complete_request()
    )

    response = report.generate(
        batch_id=batch.batch_id,
        report_request=CompanyCFOReportRequest(
            correlation_id="COMPANY-REPORT-429"
        ),
    )

    assert response.status == "FAILED"
    assert response.executed_agents == []
    assert len(response.errors) == 1
    assert response.errors[0].agent_name == "risk_ai"
    assert response.errors[0].category == "AI_RATE_LIMIT"
    assert response.errors[0].retryable is True
    assert len(provider.requests) == 1
    assert response.analysis_id is not None

    engine.dispose()


def test_company_report_api_returns_persisted_analysis():
    provider = CompanyReportProvider()
    engine, _, ingestion, report = build_report_system(
        provider
    )
    batch = ingestion.ingest(
        complete_request()
    )
    app = create_app()
    app.dependency_overrides[
        get_company_cfo_report_service
    ] = lambda: report
    client = TestClient(app)

    response = client.post(
        "/api/v1/ingestion/batches/"
        f"{batch.batch_id}/cfo-report",
        json={
            "correlation_id": "COMPANY-REPORT-API-001",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["analysis_id"]
    assert payload["final_agent"] == "chief_cfo_ai"
    assert len(payload["executed_agents"]) == 4

    engine.dispose()
