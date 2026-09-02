"""Read-only API routes for persisted CFO analyses."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from src.api.dependencies import (
    get_database_session,
)
from src.api.history_models import (
    AgentExecutionHistory,
    AnalysisHistoryDetail,
    AnalysisHistoryList,
    AnalysisHistorySummary,
    AuditLogHistory,
    BranchReference,
    CompanyReference,
)
from src.database.models import (
    AnalysisRecord,
    AuditLogRecord,
    Company,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis History"],
)


def _company_reference(
    analysis: AnalysisRecord,
) -> CompanyReference:
    """Create an API company reference."""

    if analysis.company is None:
        raise RuntimeError(
            "Persisted analysis has no company."
        )

    return CompanyReference(
        id=analysis.company.id,
        code=analysis.company.code,
        name=analysis.company.name,
        base_currency=(
            analysis.company.base_currency
        ),
    )


def _branch_reference(
    analysis: AnalysisRecord,
) -> BranchReference | None:
    """Create an optional API branch reference."""

    if analysis.branch is None:
        return None

    return BranchReference(
        id=analysis.branch.id,
        code=analysis.branch.code,
        name=analysis.branch.name,
    )


def _analysis_summary(
    analysis: AnalysisRecord,
) -> AnalysisHistorySummary:
    """Create a persisted analysis summary."""

    return AnalysisHistorySummary(
        id=analysis.id,
        correlation_id=analysis.correlation_id,
        request=analysis.request_text,
        status=analysis.status,
        company=_company_reference(
            analysis
        ),
        branch=_branch_reference(
            analysis
        ),
        final_agent=analysis.final_agent,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
    )


def _execution_history(
    execution,
) -> AgentExecutionHistory:
    """Create an API agent execution model."""

    return AgentExecutionHistory(
        id=execution.id,
        agent_name=execution.agent_name,
        sequence_number=(
            execution.sequence_number
        ),
        status=execution.status,
        input_payload=dict(
            execution.input_payload or {}
        ),
        output_payload=(
            dict(execution.output_payload)
            if execution.output_payload
            is not None
            else None
        ),
        error_category=(
            execution.error_category
        ),
        error_message=execution.error_message,
        provider_status_code=(
            execution.provider_status_code
        ),
        retryable=execution.retryable,
        prompt_tokens=execution.prompt_tokens,
        output_tokens=execution.output_tokens,
        total_tokens=execution.total_tokens,
        thought_tokens=execution.thought_tokens,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        created_at=execution.created_at,
    )


def _audit_history(
    audit_log: AuditLogRecord,
) -> AuditLogHistory:
    """Create an API audit-log model."""

    return AuditLogHistory(
        id=audit_log.id,
        action=audit_log.action,
        entity_type=audit_log.entity_type,
        entity_id=audit_log.entity_id,
        actor_type=audit_log.actor_type,
        actor_id=audit_log.actor_id,
        details=dict(
            audit_log.details or {}
        ),
        created_at=audit_log.created_at,
    )


def _resolve_company(
    *,
    session: Session,
    company_reference: str,
) -> Company:
    """Resolve a company by UUID or business code."""

    normalized_reference = (
        company_reference.strip()
    )

    company = session.get(
        Company,
        normalized_reference,
    )

    if company is None:
        statement = select(Company).where(
            Company.code
            == normalized_reference.upper()
        )

        company = session.scalar(
            statement
        )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "The requested company was not found."
            ),
        )

    return company


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisHistoryDetail,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The persisted analysis was not found."
            ),
        },
    },
)
def get_persisted_analysis(
    analysis_id: str,
    session: Annotated[
        Session,
        Depends(get_database_session),
    ],
) -> AnalysisHistoryDetail:
    """Return one complete persisted CFO analysis."""

    statement = (
        select(AnalysisRecord)
        .options(
            selectinload(
                AnalysisRecord.company
            ),
            selectinload(
                AnalysisRecord.branch
            ),
            selectinload(
                AnalysisRecord.agent_executions
            ),
        )
        .where(
            AnalysisRecord.id == analysis_id
        )
    )

    analysis = session.scalar(
        statement
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "The requested analysis was not found."
            ),
        )

    audit_statement = (
        select(AuditLogRecord)
        .where(
            AuditLogRecord.analysis_id
            == analysis.id
        )
        .order_by(
            AuditLogRecord.created_at.asc()
        )
    )

    audit_logs = list(
        session.scalars(
            audit_statement
        )
    )

    summary = _analysis_summary(
        analysis
    )

    return AnalysisHistoryDetail(
        **summary.model_dump(),
        financial_input=dict(
            analysis.financial_input or {}
        ),
        metadata=dict(
            analysis.metadata_payload or {}
        ),
        execution_plan=list(
            analysis.execution_plan or []
        ),
        executed_agents=list(
            analysis.executed_agents or []
        ),
        verified_results=dict(
            analysis.verified_results or {}
        ),
        ai_results=dict(
            analysis.ai_results or {}
        ),
        final_output=(
            dict(analysis.final_output)
            if analysis.final_output is not None
            else None
        ),
        errors=list(
            analysis.errors or []
        ),
        started_at=analysis.started_at,
        agent_executions=[
            _execution_history(
                execution
            )
            for execution
            in analysis.agent_executions
        ],
        audit_logs=[
            _audit_history(
                audit_log
            )
            for audit_log in audit_logs
        ],
    )


@router.get(
    "/companies/{company_reference}/analyses",
    response_model=AnalysisHistoryList,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The requested company was not found."
            ),
        },
    },
)
def list_company_analyses(
    company_reference: str,
    session: Annotated[
        Session,
        Depends(get_database_session),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
) -> AnalysisHistoryList:
    """Return recent persisted analyses for one company."""

    company = _resolve_company(
        session=session,
        company_reference=company_reference,
    )

    total_statement = (
        select(
            func.count(
                AnalysisRecord.id
            )
        )
        .where(
            AnalysisRecord.company_id
            == company.id
        )
    )

    total = int(
        session.scalar(
            total_statement
        )
        or 0
    )

    analyses_statement = (
        select(AnalysisRecord)
        .options(
            selectinload(
                AnalysisRecord.company
            ),
            selectinload(
                AnalysisRecord.branch
            ),
        )
        .where(
            AnalysisRecord.company_id
            == company.id
        )
        .order_by(
            AnalysisRecord.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    analyses = list(
        session.scalars(
            analyses_statement
        )
    )

    return AnalysisHistoryList(
        items=[
            _analysis_summary(
                analysis
            )
            for analysis in analyses
        ],
        total=total,
        limit=limit,
        offset=offset,
    )