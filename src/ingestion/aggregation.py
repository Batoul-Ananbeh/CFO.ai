"""Deterministic monthly aggregation of validated staging records."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.database.repositories.errors import (
    RecordNotFoundError,
)
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


UnitOfWorkFactory = Callable[
    [],
    PersistenceUnitOfWork,
]

_ACCOUNT_TYPES = {
    "ASSET",
    "LIABILITY",
    "EQUITY",
    "REVENUE",
    "EXPENSE",
}


class FinancialTotals(BaseModel):
    """Currency-specific movements derived from typed journal sides."""

    model_config = ConfigDict(extra="forbid")

    revenue: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")
    net_income: Decimal = Decimal("0")
    asset_change: Decimal = Decimal("0")
    liability_change: Decimal = Decimal("0")
    equity_change: Decimal = Decimal("0")


class MonthlyFinancialSummary(BaseModel):
    """One company or branch summary for a period and currency."""

    model_config = ConfigDict(extra="forbid")

    accounting_period: str
    currency: str
    branch_code: str | None = None
    total_transactions: int = Field(ge=0)
    classified_transactions: int = Field(ge=0)
    classification_coverage: float = Field(ge=0, le=1)
    totals: FinancialTotals


class AggregationDataProfile(BaseModel):
    """Evidence profile controlling downstream AI capabilities."""

    model_config = ConfigDict(extra="forbid")

    validation_status: str
    dataset_scope: str
    periods: list[str]
    currencies: list[str]
    expected_branch_codes: list[str]
    observed_branch_codes: list[str]
    classification_coverage: float = Field(ge=0, le=1)
    rejected_rows: int = Field(ge=0)
    verified_capabilities: list[str]
    limitations: list[str]


class MonthlyAggregationResponse(BaseModel):
    """Dashboard-ready deterministic monthly aggregation."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    company_id: str
    company_code: str
    company_summaries: list[MonthlyFinancialSummary]
    branch_summaries: list[MonthlyFinancialSummary]
    data_profile: AggregationDataProfile


class MonthlyAggregationService:
    """Aggregate only validated rows and preserve evidence limits."""

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

    def aggregate(
        self,
        batch_id: str,
    ) -> MonthlyAggregationResponse:
        """Build company, branch, and data-profile summaries."""

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
            rows = [
                record.normalized_payload
                for record in batch.staging_records
                if (
                    record.status == "VALIDATED"
                    and record.normalized_payload is not None
                )
            ]

            company_summaries = self._summaries(
                rows,
                include_branch=False,
            )
            branch_summaries = self._summaries(
                rows,
                include_branch=True,
            )
            profile = self._data_profile(
                rows=rows,
                manifest=batch.manifest,
            )

            return MonthlyAggregationResponse(
                batch_id=batch.id,
                company_id=company.id,
                company_code=company.code,
                company_summaries=company_summaries,
                branch_summaries=branch_summaries,
                data_profile=profile,
            )

    @classmethod
    def _summaries(
        cls,
        rows: list[dict[str, Any]],
        *,
        include_branch: bool,
    ) -> list[MonthlyFinancialSummary]:
        grouped: dict[
            tuple[str, str, str | None],
            list[dict[str, Any]],
        ] = defaultdict(list)

        for row in rows:
            branch_code = (
                str(row["branch_code"])
                if include_branch
                else None
            )
            key = (
                str(row["accounting_period"]),
                str(row["currency"]),
                branch_code,
            )
            grouped[key].append(row)

        summaries: list[MonthlyFinancialSummary] = []

        for (
            accounting_period,
            currency,
            branch_code,
        ), group_rows in sorted(
            grouped.items()
        ):
            classified_rows = [
                row
                for row in group_rows
                if cls._is_classified(row)
            ]
            totals = cls._totals(
                classified_rows
            )
            total_count = len(group_rows)
            classified_count = len(
                classified_rows
            )

            summaries.append(
                MonthlyFinancialSummary(
                    accounting_period=accounting_period,
                    currency=currency,
                    branch_code=branch_code,
                    total_transactions=total_count,
                    classified_transactions=classified_count,
                    classification_coverage=(
                        classified_count / total_count
                        if total_count
                        else 0
                    ),
                    totals=totals,
                )
            )

        return summaries

    @classmethod
    def _totals(
        cls,
        rows: Iterable[dict[str, Any]],
    ) -> FinancialTotals:
        values = {
            "revenue": Decimal("0"),
            "expenses": Decimal("0"),
            "asset_change": Decimal("0"),
            "liability_change": Decimal("0"),
            "equity_change": Decimal("0"),
        }

        for row in rows:
            amount = Decimal(
                str(row["amount"])
            )
            cls._apply_side(
                values,
                account_type=str(
                    row["debit_account_type"]
                ),
                amount=amount,
                is_debit=True,
            )
            cls._apply_side(
                values,
                account_type=str(
                    row["credit_account_type"]
                ),
                amount=amount,
                is_debit=False,
            )

        values["net_income"] = (
            values["revenue"]
            - values["expenses"]
        )

        return FinancialTotals(
            **values
        )

    @staticmethod
    def _apply_side(
        values: dict[str, Decimal],
        *,
        account_type: str,
        amount: Decimal,
        is_debit: bool,
    ) -> None:
        debit_sign = (
            Decimal("1")
            if is_debit
            else Decimal("-1")
        )
        credit_sign = -debit_sign

        if account_type == "ASSET":
            values["asset_change"] += (
                amount * debit_sign
            )
        elif account_type == "EXPENSE":
            values["expenses"] += (
                amount * debit_sign
            )
        elif account_type == "LIABILITY":
            values["liability_change"] += (
                amount * credit_sign
            )
        elif account_type == "EQUITY":
            values["equity_change"] += (
                amount * credit_sign
            )
        elif account_type == "REVENUE":
            values["revenue"] += (
                amount * credit_sign
            )

    @classmethod
    def _data_profile(
        cls,
        *,
        rows: list[dict[str, Any]],
        manifest: dict[str, Any],
    ) -> AggregationDataProfile:
        total_rows = len(rows)
        classified_rows = sum(
            cls._is_classified(row)
            for row in rows
        )
        coverage = (
            classified_rows / total_rows
            if total_rows
            else 0
        )
        periods = sorted(
            {
                str(row["accounting_period"])
                for row in rows
            }
        )
        currencies = sorted(
            {
                str(row["currency"])
                for row in rows
            }
        )
        observed_branches = sorted(
            {
                str(row["branch_code"])
                for row in rows
            }
        )
        expected_branches = sorted(
            manifest.get(
                "expected_branch_codes",
                [],
            )
        )
        rejected_rows = int(
            manifest.get(
                "rejected_rows",
                0,
            )
        )
        dataset_scope = str(
            manifest.get(
                "dataset_scope",
                "transaction_sample",
            )
        )
        expected_periods = cls._period_range(
            manifest.get(
                "reporting_period_start"
            ),
            manifest.get(
                "reporting_period_end"
            ),
        )

        limitations: list[str] = []
        complete_scope = (
            dataset_scope == "company_complete"
            and expected_branches == observed_branches
            and expected_periods == periods
            and len(periods) >= 3
            and rejected_rows == 0
            and coverage == 1
        )

        if dataset_scope != "company_complete":
            limitations.append(
                "Dataset scope is a transaction sample, not a declared "
                "complete company dataset."
            )
        if expected_branches != observed_branches:
            limitations.append(
                "Observed branches do not match the declared company scope."
            )
        if expected_periods != periods:
            limitations.append(
                "Observed accounting periods do not match the declared range."
            )
        if rejected_rows:
            limitations.append(
                "The ingestion batch contains rejected source rows."
            )
        if coverage < 1:
            limitations.append(
                "One or more validated transactions lack account-type "
                "classification."
            )

        capabilities = (
            [
                "multi_period_financial_history",
                "company_level_financial_context",
            ]
            if complete_scope
            else []
        )

        return AggregationDataProfile(
            validation_status="VERIFIED",
            dataset_scope=dataset_scope,
            periods=periods,
            currencies=currencies,
            expected_branch_codes=expected_branches,
            observed_branch_codes=observed_branches,
            classification_coverage=coverage,
            rejected_rows=rejected_rows,
            verified_capabilities=capabilities,
            limitations=limitations,
        )

    @staticmethod
    def _is_classified(
        row: dict[str, Any],
    ) -> bool:
        return (
            row.get("debit_account_type")
            in _ACCOUNT_TYPES
            and row.get("credit_account_type")
            in _ACCOUNT_TYPES
        )

    @staticmethod
    def _period_range(
        start: Any,
        end: Any,
    ) -> list[str]:
        if not isinstance(start, str) or not isinstance(
            end,
            str,
        ):
            return []

        start_year, start_month = map(
            int,
            start.split("-"),
        )
        end_year, end_month = map(
            int,
            end.split("-"),
        )
        periods: list[str] = []
        year = start_year
        month = start_month

        while (year, month) <= (
            end_year,
            end_month,
        ):
            periods.append(
                f"{year:04d}-{month:02d}"
            )
            month += 1

            if month == 13:
                year += 1
                month = 1

        return periods
