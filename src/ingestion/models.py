"""Public contracts for deterministic company dataset ingestion."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.schemas.enums import TransactionCategory


AccountType = Literal[
    "ASSET",
    "LIABILITY",
    "EQUITY",
    "REVENUE",
    "EXPENSE",
]


class CanonicalTransactionRow(BaseModel):
    """One normalized financial transaction accepted by CFO.ai."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    transaction_id: str = Field(min_length=1, max_length=100)
    transaction_date: date
    accounting_period: str = Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    )
    transaction_category: TransactionCategory
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    branch_code: str = Field(min_length=1, max_length=50)
    branch_name: str = Field(min_length=1, max_length=255)
    debit_account_code: str = Field(min_length=1, max_length=50)
    debit_account_name: str = Field(min_length=1, max_length=255)
    debit_account_type: AccountType | None = None
    credit_account_code: str = Field(min_length=1, max_length=50)
    credit_account_name: str = Field(min_length=1, max_length=255)
    credit_account_type: AccountType | None = None

    @field_validator(
        "currency",
        "branch_code",
        mode="after",
    )
    @classmethod
    def uppercase_codes(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_financial_consistency(
        self,
    ) -> "CanonicalTransactionRow":
        expected_period = self.transaction_date.strftime(
            "%Y-%m"
        )

        if self.accounting_period != expected_period:
            raise ValueError(
                "accounting_period must match transaction_date."
            )

        if (
            self.debit_account_code
            == self.credit_account_code
        ):
            raise ValueError(
                "debit and credit accounts must be different."
            )

        return self


class DatasetIngestionRequest(BaseModel):
    """A company dataset submitted as JSON records or CSV text."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    correlation_id: str = Field(min_length=1, max_length=100)
    company_code: str = Field(min_length=1, max_length=50)
    company_name: str = Field(min_length=1, max_length=255)
    base_currency: str = Field(min_length=3, max_length=3)
    source_name: str = Field(min_length=1, max_length=255)
    source_format: Literal["json", "csv"]
    records: list[dict[str, Any]] | None = None
    csv_content: str | None = None
    dataset_scope: Literal[
        "transaction_sample",
        "company_complete",
    ] = "transaction_sample"
    expected_branch_codes: list[str] = Field(
        default_factory=list,
    )
    reporting_period_start: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    reporting_period_end: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )

    @field_validator(
        "company_code",
        "base_currency",
        mode="after",
    )
    @classmethod
    def uppercase_codes(cls, value: str) -> str:
        return value.upper()

    @field_validator(
        "expected_branch_codes",
        mode="after",
    )
    @classmethod
    def normalize_expected_branches(
        cls,
        value: list[str],
    ) -> list[str]:
        normalized = sorted(
            {
                item.strip().upper()
                for item in value
                if item.strip()
            }
        )

        if len(normalized) != len(value):
            raise ValueError(
                "expected_branch_codes must contain unique non-empty codes."
            )

        return normalized

    @model_validator(mode="after")
    def validate_source_payload(
        self,
    ) -> "DatasetIngestionRequest":
        has_records = self.records is not None
        has_csv = bool(
            self.csv_content
            and self.csv_content.strip()
        )

        if self.source_format == "json":
            if not has_records or has_csv:
                raise ValueError(
                    "JSON ingestion requires records and forbids csv_content."
                )
        elif not has_csv or has_records:
            raise ValueError(
                "CSV ingestion requires csv_content and forbids records."
            )

        if self.dataset_scope == "company_complete":
            if not self.expected_branch_codes:
                raise ValueError(
                    "company_complete scope requires expected_branch_codes."
                )

            if (
                self.reporting_period_start is None
                or self.reporting_period_end is None
            ):
                raise ValueError(
                    "company_complete scope requires reporting period bounds."
                )

            if (
                self.reporting_period_start
                > self.reporting_period_end
            ):
                raise ValueError(
                    "reporting_period_start must not exceed "
                    "reporting_period_end."
                )

        return self


class IngestionRowError(BaseModel):
    """Public validation result for one rejected source row."""

    model_config = ConfigDict(extra="forbid")

    source_row_number: int
    transaction_id: str | None = None
    errors: list[dict[str, Any]]


class DatasetIngestionResponse(BaseModel):
    """Auditable outcome of one deterministic dataset ingestion."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    correlation_id: str
    company_id: str
    company_code: str
    status: Literal["COMPLETED", "PARTIAL", "FAILED"]
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    branch_codes: list[str]
    row_errors: list[IngestionRowError]
