"""Agent execution usage-metadata persistence tests."""

from __future__ import annotations

from src.database.base import Base
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


def test_agent_usage_is_extracted_from_ai_metadata():
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

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        company = unit_of_work.companies.create(
            code="TOKEN-COMPANY",
            name="Token Company",
            base_currency="JOD",
        )

        analysis = unit_of_work.analyses.create(
            company_id=company.id,
            correlation_id="CORR-TOKEN-001",
            request_text="Explain the journal entry",
            status="COMPLETED",
            financial_input={
                "transaction_id": "TXN-TOKEN-001",
            },
        )

        execution = (
            unit_of_work.agent_executions.create(
                analysis_id=analysis.id,
                agent_name="general_ledger_ai",
                sequence_number=1,
                status="COMPLETED",
                output_payload={
                    "summary": "Verified.",
                    "_ai_metadata": {
                        "provider": "google",
                        "usage": {
                            "prompt_tokens": 1209,
                            "output_tokens": 274,
                            "total_tokens": 2604,
                            "thought_tokens": 1121,
                        },
                    },
                },
            )
        )

        execution_id = execution.id

    with PersistenceUnitOfWork(
        session_factory
    ) as unit_of_work:
        executions = (
            unit_of_work.agent_executions
            .list_for_analysis(
                analysis.id
            )
        )

        assert len(executions) == 1
        assert executions[0].id == execution_id

        assert executions[0].prompt_tokens == 1209
        assert executions[0].output_tokens == 274
        assert executions[0].total_tokens == 2604
        assert executions[0].thought_tokens == 1121

    engine.dispose()