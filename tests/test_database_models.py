"""Persistence model tests for CFO.ai."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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


def build_database():
    """Create an isolated in-memory database."""

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


def test_database_metadata_contains_expected_tables():
    engine, _ = build_database()

    assert set(
        Base.metadata.tables
    ) >= {
        "companies",
        "branches",
        "analyses",
        "agent_executions",
        "audit_logs",
    }

    engine.dispose()


def test_company_branch_and_analysis_persist():
    engine, session_factory = build_database()

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
        correlation_id="CORR-DB-001",
        request_text="حلل مخاطر هذه العملية",
        status="COMPLETED",
        financial_input={
            "transaction_id": "TXN-001",
        },
        metadata_payload={
            "source": "test",
        },
        execution_plan=[
            "general_ledger_ai",
            "controller_ai",
            "risk_ai",
        ],
        executed_agents=[
            "general_ledger_ai",
            "controller_ai",
            "risk_ai",
        ],
        verified_results={
            "controller": {
                "status": "APPROVED",
            },
        },
        ai_results={
            "risk_ai": {
                "risk_level": "LOW",
            },
        },
        final_agent="risk_ai",
        final_output={
            "risk_level": "LOW",
        },
        errors=[],
    )

    with session_factory() as session:
        session.add(company)
        session.add(analysis)
        session.commit()

        stored_company = session.scalar(
            select(Company).where(
                Company.code == "PHARMA-GROUP"
            )
        )

        assert stored_company is not None
        assert len(stored_company.branches) == 1
        assert len(stored_company.analyses) == 1

        stored_analysis = stored_company.analyses[0]

        assert stored_analysis.branch is not None
        assert stored_analysis.branch.code == "MAIN"
        assert stored_analysis.final_agent == "risk_ai"

    engine.dispose()


def test_agent_execution_and_audit_log_persist():
    engine, session_factory = build_database()

    company = Company(
        code="COMPANY-AGENT",
        name="Agent Test Company",
        base_currency="USD",
    )

    branch = Branch(
        company=company,
        code="BRANCH-001",
        name="Test Branch",
    )

    analysis = AnalysisRecord(
        company=company,
        branch=branch,
        correlation_id="CORR-AGENT-001",
        request_text="Explain the journal entry",
        status="COMPLETED",
        financial_input={
            "transaction_id": "TXN-AGENT-001",
        },
        metadata_payload={},
        execution_plan=[
            "general_ledger_ai",
        ],
        executed_agents=[
            "general_ledger_ai",
        ],
        verified_results={},
        ai_results={},
        errors=[],
    )

    execution = AgentExecutionRecord(
        analysis=analysis,
        agent_name="general_ledger_ai",
        sequence_number=1,
        status="COMPLETED",
        input_payload={
            "transaction_id": "TXN-AGENT-001",
        },
        output_payload={
            "summary": "Journal entry explained.",
        },
        retryable=False,
        prompt_tokens=100,
        output_tokens=50,
        total_tokens=150,
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
            "final_agent": "general_ledger_ai",
        },
    )

    with session_factory() as session:
        session.add(company)
        session.add(analysis)
        session.add(execution)
        session.add(audit_log)
        session.commit()

        stored_execution = session.scalar(
            select(AgentExecutionRecord)
        )

        stored_audit_log = session.scalar(
            select(AuditLogRecord)
        )

        assert stored_execution is not None
        assert stored_execution.total_tokens == 150
        assert stored_execution.analysis is not None

        assert stored_audit_log is not None
        assert stored_audit_log.action == (
            "ANALYSIS_COMPLETED"
        )

    engine.dispose()


def test_branch_code_is_unique_within_company():
    engine, session_factory = build_database()

    company = Company(
        code="UNIQUE-COMPANY",
        name="Unique Company",
        base_currency="JOD",
    )

    branch_one = Branch(
        company=company,
        code="MAIN",
        name="Main Branch",
    )

    branch_two = Branch(
        company=company,
        code="MAIN",
        name="Duplicate Main Branch",
    )

    with session_factory() as session:
        session.add(company)
        session.add(branch_one)
        session.add(branch_two)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError(
                "Duplicate branch code should fail."
            )

    engine.dispose()
