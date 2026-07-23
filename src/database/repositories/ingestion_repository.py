"""Repository for pharmacy ingestion provenance and staging."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import (
    IngestionBatch,
    IngestionSourceFile,
    StagingRecord,
)
from src.database.repositories.errors import DuplicateRecordError


class IngestionRepository:
    """Persist batches, source files, and raw staging records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_batch(
        self,
        *,
        company_id: str,
        correlation_id: str,
        manifest: Mapping[str, Any],
        source_system: str = "oracle_datapump",
        status: str = "DISCOVERED",
    ) -> IngestionBatch:
        """Create and flush one ingestion batch."""

        batch = IngestionBatch(
            company_id=self._required_text(company_id, "Company ID"),
            correlation_id=self._required_text(
                correlation_id, "Correlation ID"
            ),
            source_system=self._required_text(
                source_system, "Source system"
            ).lower(),
            status=self._required_text(status, "Status").upper(),
            manifest=dict(manifest),
        )
        self._session.add(batch)
        self._flush_duplicate_safe(
            f"Ingestion batch {batch.correlation_id!r} already exists."
        )
        return batch

    def add_source_file(
        self,
        *,
        batch_id: str,
        branch_code: str,
        file_name: str,
        extension: str,
        byte_size: int,
        sha256: str,
        branch_id: str | None = None,
        source_metadata: Mapping[str, Any] | None = None,
    ) -> IngestionSourceFile:
        """Attach one immutable source-file identity to a batch."""

        if byte_size < 1:
            raise ValueError("Source file byte size must be positive.")

        normalized_hash = self._required_text(sha256, "SHA-256").lower()

        if len(normalized_hash) != 64:
            raise ValueError("SHA-256 must contain exactly 64 characters.")

        source_file = IngestionSourceFile(
            batch_id=self._required_text(batch_id, "Batch ID"),
            branch_id=branch_id,
            branch_code=self._required_text(
                branch_code, "Branch code"
            ).upper(),
            file_name=self._required_text(file_name, "File name"),
            extension=self._required_text(extension, "Extension").lower(),
            byte_size=byte_size,
            sha256=normalized_hash,
            source_metadata=dict(source_metadata or {}),
        )
        self._session.add(source_file)
        self._flush_duplicate_safe(
            "The source file already exists in this ingestion batch."
        )
        return source_file

    def add_staging_record(
        self,
        *,
        batch_id: str,
        source_file_id: str,
        entity_type: str,
        source_row_number: int,
        raw_payload: Mapping[str, Any],
        branch_id: str | None = None,
        source_key: str | None = None,
    ) -> StagingRecord:
        """Persist one raw, untrusted source row."""

        if source_row_number < 1:
            raise ValueError("Source row number must be at least 1.")

        staging_record = StagingRecord(
            batch_id=self._required_text(batch_id, "Batch ID"),
            source_file_id=self._required_text(
                source_file_id, "Source file ID"
            ),
            branch_id=branch_id,
            entity_type=self._required_text(
                entity_type, "Entity type"
            ).lower(),
            source_row_number=source_row_number,
            source_key=(
                self._optional_text(source_key)
                if source_key is not None
                else None
            ),
            raw_payload=dict(raw_payload),
        )
        self._session.add(staging_record)
        self._flush_duplicate_safe(
            "The source row already exists in staging."
        )
        return staging_record

    def get_batch(self, batch_id: str) -> IngestionBatch | None:
        """Return a batch with its source files and staged rows."""

        statement = (
            select(IngestionBatch)
            .options(
                selectinload(IngestionBatch.source_files),
                selectinload(IngestionBatch.staging_records),
            )
            .where(IngestionBatch.id == batch_id)
        )
        return self._session.scalar(statement)

    def list_batches_for_company(
        self, company_id: str
    ) -> list[IngestionBatch]:
        """Return newest ingestion batches for a company."""

        statement = (
            select(IngestionBatch)
            .where(IngestionBatch.company_id == company_id)
            .order_by(IngestionBatch.created_at.desc())
        )
        return list(self._session.scalars(statement))

    def _flush_duplicate_safe(self, message: str) -> None:
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateRecordError(message) from exc

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized

    @classmethod
    def _optional_text(cls, value: str) -> str | None:
        normalized = cls._required_text(value, "Optional text")
        return normalized or None
