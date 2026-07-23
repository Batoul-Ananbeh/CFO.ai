"""Regression tests for financial evidence and execution policy."""

from src.runtime.financial_accuracy import (
    FORECAST_CAPABILITY,
    STRATEGY_CAPABILITY,
    apply_execution_policy,
    assess_financial_accuracy,
)


FULL_PLAN = [
    "general_ledger_ai",
    "controller_ai",
    "risk_ai",
    "forecast_ai",
    "strategy_ai",
    "chief_cfo_ai",
]


def test_single_transaction_restricts_forecast_and_strategy() -> None:
    assessment = assess_financial_accuracy(
        metadata={
            "data_scope": "single_verified_transaction",
        }
    )

    assert assessment.data_scope == (
        "single_verified_transaction"
    )
    assert assessment.evidence_status[
        "supporting_documents"
    ] == "NOT_PROVIDED"
    assert "forecast_analysis" in assessment.restricted_analysis
    assert "strategy_analysis" in assessment.restricted_analysis

    assert apply_execution_policy(
        FULL_PLAN,
        assessment=assessment,
    ) == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "chief_cfo_ai",
    ]


def test_not_provided_is_not_rewritten_as_missing() -> None:
    assessment = assess_financial_accuracy(
        metadata={}
    )

    assert assessment.evidence_status == {
        "transaction": "PROVIDED",
        "supporting_documents": "NOT_PROVIDED",
        "multi_period_financial_history": "NOT_PROVIDED",
        "company_level_financial_context": "NOT_PROVIDED",
    }


def test_explicit_missing_document_status_is_preserved() -> None:
    assessment = assess_financial_accuracy(
        metadata={},
        verified_results={
            "data_profile": {
                "validation_status": "VERIFIED",
                "supporting_documents_status": "MISSING",
            },
        }
    )

    assert assessment.evidence_status[
        "supporting_documents"
    ] == "MISSING"


def test_verified_capabilities_enable_broader_agents() -> None:
    assessment = assess_financial_accuracy(
        metadata={},
        verified_results={
            "data_profile": {
                "validation_status": "VERIFIED",
                "verified_capabilities": [
                    FORECAST_CAPABILITY,
                    STRATEGY_CAPABILITY,
                ],
            },
        }
    )

    assert assessment.restricted_analysis == ()
    assert apply_execution_policy(
        FULL_PLAN,
        assessment=assessment,
    ) == FULL_PLAN


def test_unverified_metadata_cannot_unlock_broader_agents() -> None:
    assessment = assess_financial_accuracy(
        metadata={
            "verified_data_capabilities": [
                FORECAST_CAPABILITY,
                STRATEGY_CAPABILITY,
            ],
        },
    )

    assert "forecast_analysis" in assessment.restricted_analysis
    assert "strategy_analysis" in assessment.restricted_analysis


def test_unrelated_plan_is_not_expanded() -> None:
    assessment = assess_financial_accuracy(
        metadata={}
    )

    assert apply_execution_policy(
        ["general_ledger_ai"],
        assessment=assessment,
    ) == ["general_ledger_ai"]
