"""Financial evidence, sufficiency, and execution-policy controls."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


FORECAST_CAPABILITY = "multi_period_financial_history"
STRATEGY_CAPABILITY = "company_level_financial_context"


@dataclass(frozen=True, slots=True)
class FinancialAccuracyAssessment:
    """Auditable limits derived from explicitly supplied evidence."""

    data_scope: str
    verified_capabilities: tuple[str, ...]
    evidence_status: dict[str, str]
    permitted_analysis: tuple[str, ...]
    restricted_analysis: tuple[str, ...]
    limitations: tuple[str, ...]

    def as_context(self) -> dict[str, Any]:
        """Return JSON-compatible context for persistence and AI prompts."""

        return {
            "data_scope": self.data_scope,
            "verified_capabilities": list(
                self.verified_capabilities
            ),
            "evidence_status": dict(
                self.evidence_status
            ),
            "permitted_analysis": list(
                self.permitted_analysis
            ),
            "restricted_analysis": list(
                self.restricted_analysis
            ),
            "limitations": list(
                self.limitations
            ),
        }


def assess_financial_accuracy(
    *,
    metadata: Mapping[str, Any],
    verified_results: Mapping[str, Any] | None = None,
) -> FinancialAccuracyAssessment:
    """
    Build conservative analysis limits from explicit metadata.

    The transaction endpoint validates one accounting transaction. It must
    not silently promote that transaction into company-level evidence.
    Broader capabilities are accepted only when an upstream validated data
    pipeline declares them explicitly.
    """

    data_scope = _normalized_text(
        metadata.get("data_scope")
    ) or "single_verified_transaction"

    data_profile = _verified_data_profile(
        verified_results
    )

    verified_capabilities = _normalized_values(
        data_profile.get("verified_capabilities")
    )

    evidence_status = {
        "transaction": "PROVIDED",
        "supporting_documents": _evidence_status(
            data_profile.get("supporting_documents_status")
        ),
        "multi_period_financial_history": (
            "PROVIDED"
            if FORECAST_CAPABILITY in verified_capabilities
            else "NOT_PROVIDED"
        ),
        "company_level_financial_context": (
            "PROVIDED"
            if STRATEGY_CAPABILITY in verified_capabilities
            else "NOT_PROVIDED"
        ),
    }

    permitted = [
        "journal_entry_validation",
        "controller_review",
        "transaction_risk_screening",
        "limited_executive_brief",
    ]
    restricted: list[str] = []
    limitations: list[str] = []

    if FORECAST_CAPABILITY in verified_capabilities:
        permitted.append("forecast_analysis")
    else:
        restricted.append("forecast_analysis")
        limitations.append(
            "Forecast analysis requires verified multi-period financial "
            "history; it was not provided to this analysis."
        )

    if STRATEGY_CAPABILITY in verified_capabilities:
        permitted.append("strategy_analysis")
    else:
        restricted.append("strategy_analysis")
        limitations.append(
            "Company-level strategy requires verified company financial "
            "context; it was not provided to this analysis."
        )

    limitations.append(
        "A balanced journal entry proves debit-credit equality for that "
        "entry only; it is not a trial balance."
    )

    return FinancialAccuracyAssessment(
        data_scope=data_scope,
        verified_capabilities=tuple(
            verified_capabilities
        ),
        evidence_status=evidence_status,
        permitted_analysis=tuple(permitted),
        restricted_analysis=tuple(restricted),
        limitations=tuple(limitations),
    )


def apply_execution_policy(
    plan: Sequence[str],
    *,
    assessment: FinancialAccuracyAssessment,
) -> list[str]:
    """Remove agents whose evidence requirements are not satisfied."""

    restricted_agents: set[str] = set()

    if (
        "forecast_analysis"
        in assessment.restricted_analysis
    ):
        restricted_agents.add("forecast_ai")

    if (
        "strategy_analysis"
        in assessment.restricted_analysis
    ):
        restricted_agents.add("strategy_ai")

    return [
        agent_name
        for agent_name in plan
        if agent_name not in restricted_agents
    ]


def _normalized_values(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes),
    ):
        return []

    return sorted(
        {
            normalized
            for item in value
            if (normalized := _normalized_text(item))
        }
    )


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return value.strip().lower()


def _evidence_status(value: Any) -> str:
    normalized = _normalized_text(value).upper()

    if normalized in {
        "PROVIDED",
        "VERIFIED",
    }:
        return "PROVIDED"

    if normalized in {
        "MISSING",
        "FAILED_VERIFICATION",
    }:
        return normalized

    return "NOT_PROVIDED"


def _verified_data_profile(
    verified_results: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if not isinstance(verified_results, Mapping):
        return {}

    value = verified_results.get("data_profile")

    if not isinstance(value, Mapping):
        return {}

    if value.get("validation_status") != "VERIFIED":
        return {}

    return value
