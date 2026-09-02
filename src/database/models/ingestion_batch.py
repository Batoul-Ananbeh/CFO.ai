"""Ingestion batch persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IngestionBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track one auditable import attempt across branch source files."""

    __tablename__ = "ingestion_batches"

    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    correlation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    source_system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="oracle_datapump"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="DISCOVERED", index=True
    )
    manifest: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    company: Mapped["Company"] = relationship(
        back_populates="ingestion_batches"
    )
    source_files: Mapped[list["IngestionSourceFile"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    staging_records: Mapped[list["StagingRecord"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
