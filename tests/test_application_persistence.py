"""Application persistence integration tests for CFO.ai."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from src.ai.models import (
    AIRequest,
    AITextResult,
)
from src.ai.outputs import (
    FinancialExplanation,
)
from src.ai.provider import LLMProvider
from src.application.factory import (
    build_cfo_application_service,
)
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.database.base import Base
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import (
    DatabaseSettings,
)
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakePersistenceProvider(LLMProvider):
    """Offline provider used by persistence integration tests."""

    def __init__(self) -> None:
        self.requests: list[AIRequest] = []

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.requests.append(request)

        return AITextResult(
            content="Fake response",
            model="fake-model",
            provider="fake-provider",
        )

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        if output_schema is not FinancialExplanation:
            raise AssertionError(
                f"Unsupported schema: {output_schema}"
            )

        return output_schema.model_validate(
            {
                "summary": (
                    "The journal entry is verified."
                ),
                "key_points": [
                    "Debit equals credit.",
                ],
                "recommendations": [
                    "Continue Controller review.",
                ],
            }
        )


def valid_transaction() -> dict[str, object]:
    """Return a valid transaction."""

    return {
        "transaction_id": "TXN-PERSIST-001",
        "accounting_period": "2026-07",
        "transaction_category": "CASH_SALE",
        "description": "Persistence test transaction",
        "amount": {
            "amount": "1000.00",
            "currency": "JOD",
        },
        "debit_account": {
            "account_code": "1100",
            "account_name": "Bank",
        },
        "credit_account": {
            "account_code": "4100",
            "account_name": "Sales Revenue",
        },
    }


def build_persistent_service():
    """Build a persistent service using SQLite memory storage."""

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

    def unit_of_work_factory():
        return PersistenceUnitOfWork(
            session_factory=session_factory
        )

    persistence = AnalysisPersistenceService(
        unit_of_work_factory=unit_of_work_factory
    )

    provider = FakePersistenceProvider()

    service = build_cfo_application_service(
        provider=provider,
        persistence=persistence,
    )

    return (
        engine,
        session_factory,
        service,
        provider,
    )


def test_completed_analysis_is_persisted():
    (
        engine,
        session_factory,
        service,
        provider,
    ) = build_persistent_service()

    response = service.analyze(
        {
            "request": (
                "اشرح القيد المحاسبي"
            ),
            "financial_input": valid_transaction(),
            "metadata": {
                "correlation_id": "CORR-PERSIST-001",
                "company_id": "PHARMA-GROUP",
                "company_name": "Pharmacy Group",
                "branch_id": "MAIN",
                "branch_name": "Main Branch",
            },
        }
    )

    assert response.analysis_id is not None
    assert response.status.value == "COMPLETED"
    assert len(provider.requests) == 1

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        company = (
            unit_of_work.companies.get_by_code(
                "PHARMA-GROUP"
            )
        )

        assert company is not None

        branches = (
            unit_of_work.branches.list_for_company(
                company.id
            )
        )

        analyses = (
            unit_of_work.analyses.list_for_company(
                company.id
            )
        )

        executions = (
            unit_of_work.agent_executions
            .list_for_analysis(
                response.analysis_id
            )
        )

        audit_logs = (
            unit_of_work.audit_logs
            .list_for_analysis(
                response.analysis_id
            )
        )

        assert len(branches) == 1
        assert len(analyses) == 1
        assert len(executions) == 2
        assert len(audit_logs) == 1

        assert executions[0].agent_name == (
            "deterministic_finance"
        )

        assert executions[1].agent_name == (
            "general_ledger_ai"
        )

        assert analyses[0].final_agent == (
            "general_ledger_ai"
        )

    engine.dispose()


def test_existing_company_and_branch_are_reused():
    (
        engine,
        session_factory,
        service,
        _,
    ) = build_persistent_service()

    common_metadata = {
        "company_id": "PHARMA-GROUP",
        "company_name": "Pharmacy Group",
        "branch_id": "MAIN",
        "branch_name": "Main Branch",
    }

    service.analyze(
        {
            "request": "اشرح القيد المحاسبي",
            "financial_input": valid_transaction(),
            "metadata": {
                **common_metadata,
                "correlation_id": "CORR-PERSIST-002",
            },
        }
    )

    second_transaction = valid_transaction()
    second_transaction[
        "transaction_id"
    ] = "TXN-PERSIST-002"

    service.analyze(
        {
            "request": "اشرح القيد المحاسبي",
            "financial_input": second_transaction,
            "metadata": {
                **common_metadata,
                "correlation_id": "CORR-PERSIST-003",
            },
        }
    )

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        companies = (
            unit_of_work.companies.list_active()
        )

        assert len(companies) == 1

        branches = (
            unit_of_work.branches.list_for_company(
                companies[0].id
            )
        )

        analyses = (
            unit_of_work.analyses.list_for_company(
                companies[0].id
            )
        )

        assert len(branches) == 1
        assert len(analyses) == 2

    engine.dispose()


def test_failed_deterministic_analysis_is_persisted():
    (
        engine,
        session_factory,
        service,
        provider,
    ) = build_persistent_service()

    invalid_transaction = valid_transaction()

    invalid_transaction[
        "credit_account"
    ] = {
        "account_code": "1100",
        "account_name": "Bank",
    }

    response = service.analyze(
        {
            "request": "حلل مخاطر العملية",
            "financial_input": invalid_transaction,
            "metadata": {
                "correlation_id": "CORR-PERSIST-FAILED",
                "company_id": "FAILED-COMPANY",
            },
        }
    )

    assert response.analysis_id is not None
    assert response.status.value == "FAILED"
    assert len(provider.requests) == 0

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        executions = (
            unit_of_work.agent_executions
            .list_for_analysis(
                response.analysis_id
            )
        )

        assert len(executions) == 4

        assert executions[0].agent_name == (
            "deterministic_finance"
        )

        assert executions[0].status == "FAILED"

        assert [
            execution.status
            for execution in executions[1:]
        ] == [
            "SKIPPED",
            "SKIPPED",
            "SKIPPED",
        ]

    engine.dispose()


def test_service_without_persistence_remains_supported():
    provider = FakePersistenceProvider()

    service = build_cfo_application_service(
        provider=provider
    )

    response = service.analyze(
        {
            "request": "اشرح القيد المحاسبي",
            "financial_input": valid_transaction(),
        }
    )

    assert response.analysis_id is None
    assert response.correlation_id is not None
    assert response.status.value == "COMPLETED"