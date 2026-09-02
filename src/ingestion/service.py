"""Deterministic ingestion service for canonical company datasets."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from pydantic import ValidationError

from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.database.repositories.errors import (
    RecordNotFoundError,
)
from src.ingestion.models import (
    CanonicalTransactionRow,
    DatasetIngestionRequest,
    DatasetIngestionResponse,
    IngestionRowError,
)


UnitOfWorkFactory = Callable[
    [],
    PersistenceUnitOfWork,
]


class DatasetMappingConflictError(ValueError):
    """Raised when a dataset conflicts with an existing company mapping."""


class DatasetIngestionService:
    """Validate, map, and stage one company financial dataset."""

    def __init__(
        self,
        *,
        unit_of_work_factory: UnitOfWorkFactory | None = None,
    ) -> None:
        self._unit_of_work_factory = (
            unit_of_work_factory
            if unit_of_work_factory is not None
            else PersistenceUnitOfWork
        )

    def ingest(
        self,
        request: DatasetIngestionRequest,
    ) -> DatasetIngestionResponse:
        """Persist an auditable batch while retaining rejected rows."""

        rows, first_row_number = self._read_rows(
            request
        )
        source_bytes = self._source_bytes(
            request
        )

        accepted_rows = 0
        row_errors: list[IngestionRowError] = []
        branch_codes: set[str] = set()
        seen_transaction_ids: set[str] = set()

        with self._unit_of_work_factory() as unit_of_work:
            company = unit_of_work.companies.get_by_code(
                request.company_code
            )

            if company is None:
                company = unit_of_work.companies.create(
                    code=request.company_code,
                    name=request.company_name,
                    base_currency=request.base_currency,
                )
            elif (
                company.base_currency
                != request.base_currency
            ):
                raise DatasetMappingConflictError(
                    "The supplied base currency conflicts with the "
                    "existing company mapping."
                )

            batch = unit_of_work.ingestion.create_batch(
                company_id=company.id,
                correlation_id=request.correlation_id,
                source_system="canonical_dataset",
                status="VALIDATING",
                manifest={
                    "contract_version": "1.0",
                    "source_format": request.source_format,
                    "source_name": request.source_name,
                    "total_rows": len(rows),
                    "dataset_scope": request.dataset_scope,
                    "expected_branch_codes": (
                        request.expected_branch_codes
                    ),
                    "reporting_period_start": (
                        request.reporting_period_start
                    ),
                    "reporting_period_end": (
                        request.reporting_period_end
                    ),
                },
            )
            batch.started_at = datetime.now(
                timezone.utc
            )

            source_file = unit_of_work.ingestion.add_source_file(
                batch_id=batch.id,
                branch_code="MULTI",
                file_name=request.source_name,
                extension=f".{request.source_format}",
                byte_size=max(1, len(source_bytes)),
                sha256=sha256(source_bytes).hexdigest(),
                source_metadata={
                    "contract_version": "1.0",
                    "encoding": "utf-8",
                },
            )

            for offset, raw_row in enumerate(rows):
                row_number = first_row_number + offset
                validation_errors: list[dict[str, Any]] = []
                normalized_row: CanonicalTransactionRow | None = None

                try:
                    normalized_row = (
                        CanonicalTransactionRow.model_validate(
                            raw_row
                        )
                    )
                except ValidationError as exc:
                    validation_errors.extend(
                        self._public_validation_errors(
                            exc
                        )
                    )

                transaction_id = self._transaction_id(
                    raw_row
                )

                if (
                    normalized_row is not None
                    and normalized_row.transaction_id
                    in seen_transaction_ids
                ):
                    validation_errors.append(
                        {
                            "field": "transaction_id",
                            "code": "DUPLICATE_IN_DATASET",
                            "message": (
                                "transaction_id must be unique "
                                "within the dataset."
                            ),
                        }
                    )

                branch = None

                if (
                    normalized_row is not None
                    and not validation_errors
                ):
                    seen_transaction_ids.add(
                        normalized_row.transaction_id
                    )
                    branch = (
                        unit_of_work.branches
                        .get_by_company_and_code(
                            company_id=company.id,
                            code=normalized_row.branch_code,
                        )
                    )

                    if branch is None:
                        branch = unit_of_work.branches.create(
                            company_id=company.id,
                            code=normalized_row.branch_code,
                            name=normalized_row.branch_name,
                        )

                    branch_codes.add(branch.code)

                staging_record = (
                    unit_of_work.ingestion.add_staging_record(
                        batch_id=batch.id,
                        source_file_id=source_file.id,
                        branch_id=(
                            branch.id
                            if branch is not None
                            else None
                        ),
                        entity_type="financial_transaction",
                        source_row_number=row_number,
                        source_key=transaction_id,
                        raw_payload=raw_row,
                    )
                )

                if (
                    normalized_row is not None
                    and not validation_errors
                ):
                    staging_record.normalized_payload = (
                        normalized_row.model_dump(
                            mode="json"
                        )
                    )
                    staging_record.status = "VALIDATED"
                    accepted_rows += 1
                else:
                    staging_record.status = "REJECTED"
                    staging_record.validation_errors = (
                        validation_errors
                    )
                    row_errors.append(
                        IngestionRowError(
                            source_row_number=row_number,
                            transaction_id=transaction_id,
                            errors=validation_errors,
                        )
                    )

            total_rows = len(rows)
            rejected_rows = total_rows - accepted_rows
            status = self._batch_status(
                accepted_rows=accepted_rows,
                rejected_rows=rejected_rows,
            )
            batch.status = status
            batch.completed_at = datetime.now(
                timezone.utc
            )
            batch.manifest = {
                **batch.manifest,
                "accepted_rows": accepted_rows,
                "rejected_rows": rejected_rows,
                "branch_codes": sorted(
                    branch_codes
                ),
            }

            result = DatasetIngestionResponse(
                batch_id=batch.id,
                correlation_id=batch.correlation_id,
                company_id=company.id,
                company_code=company.code,
                status=status,
                total_rows=total_rows,
                accepted_rows=accepted_rows,
                rejected_rows=rejected_rows,
                branch_codes=sorted(branch_codes),
                row_errors=row_errors,
            )

        return result

    def get_batch(
        self,
        batch_id: str,
    ) -> DatasetIngestionResponse:
        """Return a previously persisted ingestion result."""

        with self._unit_of_work_factory() as unit_of_work:
            batch = unit_of_work.ingestion.get_batch(
                batch_id
            )

            if batch is None:
                raise RecordNotFoundError(
                    f"Ingestion batch {batch_id!r} was not found."
                )

            company = unit_of_work.companies.require_by_id(
                batch.company_id
            )
            records = sorted(
                batch.staging_records,
                key=lambda record: (
                    record.source_row_number
                ),
            )
            rejected = [
                record
                for record in records
                if record.status == "REJECTED"
            ]

            return DatasetIngestionResponse(
                batch_id=batch.id,
                correlation_id=batch.correlation_id,
                company_id=company.id,
                company_code=company.code,
                status=batch.status,
                total_rows=len(records),
                accepted_rows=sum(
                    record.status == "VALIDATED"
                    for record in records
                ),
                rejected_rows=len(rejected),
                branch_codes=list(
                    batch.manifest.get(
                        "branch_codes",
                        [],
                    )
                ),
                row_errors=[
                    IngestionRowError(
                        source_row_number=(
                            record.source_row_number
                        ),
                        transaction_id=record.source_key,
                        errors=record.validation_errors,
                    )
                    for record in rejected
                ],
            )

    @staticmethod
    def _read_rows(
        request: DatasetIngestionRequest,
    ) -> tuple[list[dict[str, Any]], int]:
        if request.source_format == "json":
            return list(request.records or []), 1

        reader = csv.DictReader(
            io.StringIO(
                request.csv_content or ""
            )
        )

        if reader.fieldnames is None:
            raise ValueError(
                "CSV content must contain a header row."
            )

        return [
            dict(row)
            for row in reader
        ], 2

    @staticmethod
    def _source_bytes(
        request: DatasetIngestionRequest,
    ) -> bytes:
        if request.source_format == "csv":
            content = request.csv_content or ""
        else:
            content = json.dumps(
                request.records,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )

        return content.encode("utf-8")

    @staticmethod
    def _transaction_id(
        raw_row: dict[str, Any],
    ) -> str | None:
        value = raw_row.get(
            "transaction_id"
        )

        if not isinstance(value, str):
            return None

        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _public_validation_errors(
        error: ValidationError,
    ) -> list[dict[str, Any]]:
        return [
            {
                "field": ".".join(
                    str(part)
                    for part in issue["loc"]
                ) or "row",
                "code": issue["type"],
                "message": issue["msg"],
            }
            for issue in error.errors(
                include_url=False,
                include_input=False,
                include_context=False,
            )
        ]

    @staticmethod
    def _batch_status(
        *,
        accepted_rows: int,
        rejected_rows: int,
    ) -> str:
        if accepted_rows and not rejected_rows:
            return "COMPLETED"

        if accepted_rows:
            return "PARTIAL"

        return "FAILED"
