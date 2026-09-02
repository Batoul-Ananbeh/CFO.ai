"""CFO analysis persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class AnalysisRecord(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """Persist one complete CFO analysis request and result."""

    __tablename__ = "analyses"

    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    correlation_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    request_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    financial_input: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    execution_plan: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    executed_agents: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    verified_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    ai_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    final_agent: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    final_output: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    company: Mapped["Company"] = relationship(
        back_populates="analyses",
    )

    branch: Mapped["Branch | None"] = relationship(
        back_populates="analyses",
    )

    agent_executions: Mapped[
        list["AgentExecutionRecord"]
    ] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AgentExecutionRecord.sequence_number",
    )
