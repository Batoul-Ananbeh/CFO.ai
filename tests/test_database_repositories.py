"""Repository and unit-of-work tests for CFO.ai."""

from __future__ import annotations

import pytest

from src.database.base import Base
from src.database.repositories.errors import (
    DuplicateRecordError,
)
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


def build_database():
    """Create an isolated repository test database."""

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

    return engine, session_factory


def test_company_and_branch_repositories():
    engine, session_factory = build_database()

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        company = unit_of_work.companies.create(
            code="pharma-group",
            name="Pharmacy Group",
            base_currency="jod",
        )

        branch = unit_of_work.branches.create(
            company_id=company.id,
            code="main",
            name="Main Branch",
        )

        company_id = company.id
        branch_id = branch.id

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        stored_company = (
            unit_of_work.companies.require_by_id(
                company_id
            )
        )

        stored_branch = (
            unit_of_work.branches.require_by_id(
                branch_id
            )
        )

        assert stored_company.code == "PHARMA-GROUP"
        assert stored_company.base_currency == "JOD"
        assert stored_branch.code == "MAIN"

        assert len(
            unit_of_work.branches.list_for_company(
                company_id
            )
        ) == 1

    engine.dispose()


def test_duplicate_company_code_is_rejected():
    engine, session_factory = build_database()

    with pytest.raises(
        DuplicateRecordError
    ):
        with PersistenceUnitOfWork(
            session_factory
        ) as unit_of_work:
            unit_of_work.companies.create(
                code="DUPLICATE",
                name="First Company",
            )

            unit_of_work.companies.create(
                code="duplicate",
                name="Second Company",
            )

    engine.dispose()


def test_analysis_agent_execution_and_audit_persist():
    engine, session_factory = build_database()

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        company = unit_of_work.companies.create(
            code="COMPANY-001",
            name="CFO Test Company",
            base_currency="USD",
        )

        branch = unit_of_work.branches.create(
            company_id=company.id,
            code="BRANCH-001",
            name="Test Branch",
        )

        analysis = unit_of_work.analyses.create(
            company_id=company.id,
            branch_id=branch.id,
            correlation_id="CORR-REPO-001",
            request_text="Analyze this transaction",
            status="COMPLETED",
            financial_input={
                "transaction_id": "TXN-001",
            },
            execution_plan=[
                "general_ledger_ai",
            ],
            executed_agents=[
                "general_ledger_ai",
            ],
            verified_results={
                "controller": {
                    "status": "APPROVED",
                },
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
        )

        unit_of_work.agent_executions.create(
            analysis_id=analysis.id,
            agent_name="general_ledger_ai",
            sequence_number=1,
            status="COMPLETED",
            input_payload={
                "transaction_id": "TXN-001",
            },
            output_payload={
                "summary": "Verified.",
            },
            prompt_tokens=100,
            output_tokens=25,
            total_tokens=125,
        )

        unit_of_work.audit_logs.create(
            company_id=company.id,
            branch_id=branch.id,
            analysis_id=analysis.id,
            action="ANALYSIS_COMPLETED",
            entity_type="analysis",
            entity_id=analysis.id,
            details={
                "status": "COMPLETED",
            },
        )

        company_id = company.id
        analysis_id = analysis.id

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        analyses = (
            unit_of_work.analyses.list_for_company(
                company_id
            )
        )

        executions = (
            unit_of_work.agent_executions
            .list_for_analysis(
                analysis_id
            )
        )

        audit_logs = (
            unit_of_work.audit_logs
            .list_for_analysis(
                analysis_id
            )
        )

        assert len(analyses) == 1
        assert analyses[0].final_agent == (
            "general_ledger_ai"
        )

        assert len(executions) == 1
        assert executions[0].total_tokens == 125

        assert len(audit_logs) == 1
        assert audit_logs[0].action == (
            "ANALYSIS_COMPLETED"
        )

    engine.dispose()


def test_analysis_correlation_id_is_unique():
    engine, session_factory = build_database()

    with pytest.raises(
        DuplicateRecordError
    ):
        with PersistenceUnitOfWork(
            session_factory
        ) as unit_of_work:
            company = unit_of_work.companies.create(
                code="ANALYSIS-COMPANY",
                name="Analysis Company",
            )

            common_arguments = {
                "company_id": company.id,
                "correlation_id": "CORR-DUPLICATE",
                "request_text": "Analyze",
                "status": "COMPLETED",
                "financial_input": {},
            }

            unit_of_work.analyses.create(
                **common_arguments
            )

            unit_of_work.analyses.create(
                **common_arguments
            )

    engine.dispose()


def test_unit_of_work_rolls_back_on_error():
    engine, session_factory = build_database()

    with pytest.raises(
        RuntimeError,
        match="Force transaction rollback",
    ):
        with PersistenceUnitOfWork(
            session_factory
        ) as unit_of_work:
            unit_of_work.companies.create(
                code="ROLLBACK-COMPANY",
                name="Rollback Company",
            )

            raise RuntimeError(
                "Force transaction rollback"
            )

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        company = (
            unit_of_work.companies.get_by_code(
                "ROLLBACK-COMPANY"
            )
        )

        assert company is None

    engine.dispose()