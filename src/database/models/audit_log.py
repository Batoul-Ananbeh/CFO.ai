"""Audit log persistence model for CFO.ai."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class AuditLogRecord(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """Persist an immutable business or system audit event."""

    __tablename__ = "audit_logs"

    company_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "companies.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    branch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "branches.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    analysis_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "analyses.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    actor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SYSTEM",
    )

    actor_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    company: Mapped["Company | None"] = relationship()
    branch: Mapped["Branch | None"] = relationship()
    analysis: Mapped["AnalysisRecord | None"] = relationship()
