"""Audit log repository for CFO.ai."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import AuditLogRecord


class AuditLogRepository:
    """Persist and query CFO.ai audit events."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        *,
        action: str,
        entity_type: str,
        details: dict[str, Any] | None = None,
        company_id: str | None = None,
        branch_id: str | None = None,
        analysis_id: str | None = None,
        entity_id: str | None = None,
        actor_type: str = "SYSTEM",
        actor_id: str | None = None,
    ) -> AuditLogRecord:
        """Create and flush an immutable audit event."""

        audit_log = AuditLogRecord(
            company_id=company_id,
            branch_id=branch_id,
            analysis_id=analysis_id,
            action=action.strip().upper(),
            entity_type=entity_type.strip().lower(),
            entity_id=entity_id,
            actor_type=actor_type.strip().upper(),
            actor_id=actor_id,
            details=dict(
                details or {}
            ),
        )

        self._session.add(audit_log)
        self._session.flush()

        return audit_log

    def list_for_analysis(
        self,
        analysis_id: str,
    ) -> list[AuditLogRecord]:
        """Return audit events for one analysis."""

        statement = (
            select(AuditLogRecord)
            .where(
                AuditLogRecord.analysis_id
                == analysis_id
            )
            .order_by(
                AuditLogRecord.created_at.asc()
            )
        )

        return list(
            self._session.scalars(
                statement
            )
        )