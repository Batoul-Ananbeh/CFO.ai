"""Cost-aware verified context for company-level CFO reports."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any


_TOTAL_FIELDS = (
    "revenue",
    "expenses",
    "net_income",
    "asset_change",
    "liability_change",
    "equity_change",
)


def build_company_report_context(
    aggregation_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Keep monthly company trends and replace verbose branch-month rows with
    deterministic branch totals. Currency groups are always kept separate.
    """

    return {
        "batch_id": aggregation_payload["batch_id"],
        "company_id": aggregation_payload["company_id"],
        "company_code": aggregation_payload["company_code"],
        "data_profile": aggregation_payload["data_profile"],
        "company_monthly_summaries": aggregation_payload[
            "company_summaries"
        ],
        "branch_currency_totals": _branch_currency_totals(
            aggregation_payload["branch_summaries"]
        ),
        "context_policy": {
            "name": "cost_optimized_company_report_v1",
            "company_monthly_history_preserved": True,
            "branch_monthly_rows_replaced_by_totals": True,
            "currencies_kept_separate": True,
        },
    }


def _branch_currency_totals(
    branch_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str],
        dict[str, Any],
    ] = defaultdict(
        lambda: {
            "periods": set(),
            "total_transactions": 0,
            "classified_transactions": 0,
            "totals": {
                field: Decimal("0")
                for field in _TOTAL_FIELDS
            },
        }
    )

    for summary in branch_summaries:
        key = (
            str(summary["branch_code"]),
            str(summary["currency"]),
        )
        target = grouped[key]
        target["periods"].add(
            str(summary["accounting_period"])
        )
        target["total_transactions"] += int(
            summary["total_transactions"]
        )
        target["classified_transactions"] += int(
            summary["classified_transactions"]
        )

        for field in _TOTAL_FIELDS:
            target["totals"][field] += Decimal(
                str(summary["totals"][field])
            )

    results: list[dict[str, Any]] = []

    for (branch_code, currency), values in sorted(
        grouped.items()
    ):
        total_transactions = values["total_transactions"]
        classified_transactions = values[
            "classified_transactions"
        ]
        results.append(
            {
                "branch_code": branch_code,
                "currency": currency,
                "periods": sorted(values["periods"]),
                "total_transactions": total_transactions,
                "classified_transactions": classified_transactions,
                "classification_coverage": (
                    classified_transactions / total_transactions
                    if total_transactions
                    else 0
                ),
                "totals": {
                    field: str(value)
                    for field, value in values["totals"].items()
                },
            }
        )

    return results
