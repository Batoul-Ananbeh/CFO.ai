"""CFO analysis repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import AnalysisRecord
from src.database.repositories.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
)


class AnalysisRepository:
    """Persist and query CFO analysis records."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        *,
        company_id: str,
        correlation_id: str,
        request_text: str,
        status: str,
        financial_input: dict[str, Any],
        metadata_payload: dict[str, Any] | None = None,
        execution_plan: list[str] | None = None,
        executed_agents: list[str] | None = None,
        verified_results: dict[str, Any] | None = None,
        ai_results: dict[str, Any] | None = None,
        final_agent: str | None = None,
        final_output: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
        branch_id: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> AnalysisRecord:
        """Create and flush an analysis record."""

        analysis = AnalysisRecord(
            company_id=company_id,
            branch_id=branch_id,
            correlation_id=(
                self._normalize_required_text(
                    correlation_id,
                    field_name="Correlation ID",
                )
            ),
            request_text=(
                self._normalize_required_text(
                    request_text,
                    field_name="Request text",
                )
            ),
            status=self._normalize_status(
                status
            ),
            financial_input=dict(
                financial_input
            ),
            metadata_payload=dict(
                metadata_payload or {}
            ),
            execution_plan=list(
                execution_plan or []
            ),
            executed_agents=list(
                executed_agents or []
            ),
            verified_results=dict(
                verified_results or {}
            ),
            ai_results=dict(
                ai_results or {}
            ),
            final_agent=final_agent,
            final_output=(
                dict(final_output)
                if final_output is not None
                else None
            ),
            errors=list(
                errors or []
            ),
            started_at=started_at,
            completed_at=completed_at,
        )

        self._session.add(analysis)

        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateRecordError(
                "Analysis correlation ID "
                f"{analysis.correlation_id!r} already exists."
            ) from exc

        return analysis

    def get_by_id(
        self,
        analysis_id: str,
    ) -> AnalysisRecord | None:
        """Return an analysis by primary key."""

        return self._session.get(
            AnalysisRecord,
            analysis_id,
        )

    def require_by_id(
        self,
        analysis_id: str,
    ) -> AnalysisRecord:
        """Return an analysis or raise a structured error."""

        analysis = self.get_by_id(
            analysis_id
        )

        if analysis is None:
            raise RecordNotFoundError(
                f"Analysis {analysis_id!r} was not found."
            )

        return analysis

    def get_by_correlation_id(
        self,
        correlation_id: str,
    ) -> AnalysisRecord | None:
        """Return an analysis by correlation ID."""

        statement = select(
            AnalysisRecord
        ).where(
            AnalysisRecord.correlation_id
            == correlation_id.strip()
        )

        return self._session.scalar(
            statement
        )

    def list_for_company(
        self,
        company_id: str,
        *,
        limit: int = 100,
    ) -> list[AnalysisRecord]:
        """Return recent company analyses."""

        if limit < 1:
            raise ValueError(
                "Analysis list limit must be at least 1."
            )

        statement = (
            select(AnalysisRecord)
            .where(
                AnalysisRecord.company_id
                == company_id
            )
            .order_by(
                AnalysisRecord.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self._session.scalars(
                statement
            )
        )

    @staticmethod
    def _normalize_status(
        value: str,
    ) -> str:
        """Normalize an analysis status."""

        return AnalysisRepository._normalize_required_text(
            value,
            field_name="Analysis status",
        ).upper()

    @staticmethod
    def _normalize_required_text(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """Normalize required text input."""

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized_value