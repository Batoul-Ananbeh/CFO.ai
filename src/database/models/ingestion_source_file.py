"""Ingestion source-file persistence model."""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IngestionSourceFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Preserve the identity and branch provenance of one source file."""

    __tablename__ = "ingestion_source_files"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "sha256",
            name="uq_ingestion_source_files_batch_hash",
        ),
    )

    batch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingestion_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    branch_code: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    batch: Mapped["IngestionBatch"] = relationship(
        back_populates="source_files"
    )
    branch: Mapped["Branch | None"] = relationship()
    staging_records: Mapped[list["StagingRecord"]] = relationship(
        back_populates="source_file",
        passive_deletes=True,
    )
