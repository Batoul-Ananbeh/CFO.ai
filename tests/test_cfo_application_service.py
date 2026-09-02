"""Tests for the CFO.ai application service."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, TypeVar

from pydantic import BaseModel

from src.ai.models import (
    AIRequest,
    AITextResult,
)
from src.ai.outputs import (
    ChiefCFOBrief,
    ControllerReview,
    FinancialExplanation,
    ForecastAnalysis,
    RiskAssessment,
    StrategyAnalysis,
)
from src.ai.provider import LLMProvider
from src.application.factory import (
    build_cfo_application_service,
)
from src.application.models import (
    CFOAnalysisRequest,
)
from src.runtime.models import (
    HybridRuntimeStatus,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakeApplicationProvider(LLMProvider):
    """Fake provider for application-layer tests."""

    def __init__(self) -> None:
        self.requests: list[AIRequest] = []

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.requests.append(request)

        return AITextResult(
            content="Fake application response",
            model="fake-model",
            provider="fake-provider",
        )

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        payloads: dict[
            type[BaseModel],
            dict[str, Any],
        ] = {
            FinancialExplanation: {
                "summary": "The journal entry is verified.",
                "key_points": [
                    "Debit equals credit.",
                ],
                "recommendations": [
                    "Continue Controller review.",
                ],
            },
            ControllerReview: {
                "summary": "The Controller review is complete.",
                "control_findings": [
                    "The journal entry is balanced.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain supporting evidence.",
                ],
            },
            RiskAssessment: {
                "summary": "The current risk is low.",
                "risk_level": "LOW",
                "risk_findings": [
                    "No accounting imbalance exists.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Continue reconciliation.",
                ],
            },
            ForecastAnalysis: {
                "summary": "The outlook is stable.",
                "assumptions": [
                    "Current activity remains stable.",
                ],
                "expected_scenario": [
                    "Liquidity remains positive.",
                ],
                "downside_risks": [
                    "Unexpected expense growth.",
                ],
                "recommendations": [
                    "Monitor cash movement.",
                ],
            },
            StrategyAnalysis: {
                "summary": "Liquidity is the priority.",
                "strategic_priorities": [
                    "Protect operational cash.",
                ],
                "recommended_actions": [
                    "Review nonessential spending.",
                ],
                "expected_benefits": [
                    "Improved cash runway.",
                ],
                "risks_and_tradeoffs": [
                    "Cost controls may limit growth.",
                ],
            },
            ChiefCFOBrief: {
                "executive_summary": (
                    "The verified financial position is stable."
                ),
                "key_financial_signals": [
                    "The journal entry is approved.",
                ],
                "critical_risks": [],
                "recommended_decisions": [
                    "Continue monthly monitoring.",
                ],
                "human_approvals_required": [
                    "Final financial approval.",
                ],
            },
        }

        payload = payloads.get(
            output_schema
        )

        if payload is None:
            raise AssertionError(
                f"Unsupported schema: {output_schema}"
            )

        return output_schema.model_validate(
            payload
        )


def valid_transaction() -> dict[str, Any]:
    """Return valid raw financial input."""

    return {
        "transaction_id": "TXN-APP-001",
        "accounting_period": "2026-07",
        "transaction_category": "CASH_SALE",
        "description": (
            "Cash sale processed through application service"
        ),
        "amount": {
            "amount": Decimal("1500.00"),
            "currency": "USD",
        },
        "debit_account": {
            "account_code": "1100",
            "account_name": "Bank",
        },
        "credit_account": {
            "account_code": "4100",
            "account_name": "Sales Revenue",
        },
    }


def test_service_runs_risk_analysis():
    provider = FakeApplicationProvider()

    service = build_cfo_application_service(
        provider=provider
    )

    response = service.analyze(
        {
            "request": (
                "\u062d\u0644\u0644 "
                "\u0645\u062e\u0627\u0637\u0631 "
                "\u0647\u0630\u0647 "
                "\u0627\u0644\u0639\u0645\u0644\u064a\u0629"
            ),
            "financial_input": valid_transaction(),
            "metadata": {
                "correlation_id": "CORR-APP-001",
                "company_id": "COMPANY-001",
            },
        }
    )

    assert response.status is (
        HybridRuntimeStatus.COMPLETED
    )

    assert response.correlation_id == (
        "CORR-APP-001"
    )

    assert response.executed_agents == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    ]

    assert response.final_agent == "risk_ai"

    assert response.final_output == (
        response.ai_results["risk_ai"]
    )

    assert len(provider.requests) == 3
    assert response.errors == []


def test_service_runs_complete_cfo_report():
    provider = FakeApplicationProvider()

    service = build_cfo_application_service(
        provider=provider
    )

    response = service.analyze(
        CFOAnalysisRequest(
            request=(
                "\u0627\u0639\u0637\u0646\u064a "
                "\u062a\u0642\u0631\u064a\u0631 CFO "
                "\u0643\u0627\u0645\u0644"
            ),
            financial_input=valid_transaction(),
        )
    )

    assert response.status is (
        HybridRuntimeStatus.COMPLETED
    )

    assert response.executed_agents == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "chief_cfo_ai",
    ]
    assert len(provider.requests) == 4

    assert response.verified_results[
        "data_sufficiency"
    ]["restricted_analysis"] == [
        "forecast_analysis",
        "strategy_analysis",
    ]

    assert response.final_agent == (
        "chief_cfo_ai"
    )

    assert response.final_output is not None

    assert response.final_output[
        "executive_summary"
    ] == (
        "The verified financial position is stable."
    )


def test_service_returns_failed_response_for_invalid_input():
    provider = FakeApplicationProvider()

    service = build_cfo_application_service(
        provider=provider
    )

    invalid_transaction = valid_transaction()

    invalid_transaction[
        "credit_account"
    ] = {
        "account_code": "1100",
        "account_name": "Bank",
    }

    response = service.analyze(
        {
            "request": (
                "\u062d\u0644\u0644 "
                "\u0645\u062e\u0627\u0637\u0631 "
                "\u0627\u0644\u0639\u0645\u0644\u064a\u0629"
            ),
            "financial_input": invalid_transaction,
        }
    )

    assert response.status is (
        HybridRuntimeStatus.FAILED
    )

    assert response.executed_agents == []
    assert response.final_agent is None
    assert response.final_output is None
    assert len(provider.requests) == 0
    assert len(response.errors) == 1

    assert response.errors[0].agent_name == (
        "deterministic_finance"
    )


def test_service_response_is_json_serializable():
    provider = FakeApplicationProvider()

    service = build_cfo_application_service(
        provider=provider
    )

    payload = service.analyze_to_dict(
        {
            "request": (
                "\u0627\u0634\u0631\u062d "
                "\u0627\u0644\u0642\u064a\u062f "
                "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a"
            ),
            "financial_input": valid_transaction(),
        }
    )

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
    )

    assert isinstance(serialized, str)
    assert payload["status"] == "COMPLETED"

    assert payload["final_agent"] == (
        "general_ledger_ai"
    )


def test_request_model_normalizes_whitespace():
    analysis_request = CFOAnalysisRequest(
        request=(
            "   Review the financial risk.   "
        ),
        financial_input=valid_transaction(),
    )

    assert analysis_request.request == (
        "Review the financial risk."
    )
