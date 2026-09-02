"""Agent execution persistence model for CFO.ai."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class AgentExecutionRecord(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """Persist one agent execution inside a CFO analysis."""

    __tablename__ = "agent_executions"

    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "sequence_number",
            name="uq_agent_executions_analysis_sequence",
        ),
    )

    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "analyses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    input_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    output_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    provider_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    retryable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    thought_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    analysis: Mapped["AnalysisRecord"] = relationship(
        back_populates="agent_executions",
    )
