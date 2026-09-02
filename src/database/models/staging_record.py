"""Raw staging-record persistence model."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StagingRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store a source row before it is trusted or promoted to core finance."""

    __tablename__ = "staging_records"
    __table_args__ = (
        UniqueConstraint(
            "source_file_id",
            "entity_type",
            "source_row_number",
            name="uq_staging_records_source_entity_row",
        ),
    )

    batch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingestion_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_file_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingestion_source_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="RAW", index=True
    )
    validation_errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    batch: Mapped["IngestionBatch"] = relationship(
        back_populates="staging_records"
    )
    source_file: Mapped["IngestionSourceFile"] = relationship(
        back_populates="staging_records"
    )
    branch: Mapped["Branch | None"] = relationship()
