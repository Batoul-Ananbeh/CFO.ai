"""End-to-end tests for real CFO AI agents with a fake provider."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from src.ai.models import AIRequest, AITextResult
from src.ai.outputs import (
    ChiefCFOBrief,
    ControllerReview,
    FinancialExplanation,
    ForecastAnalysis,
    RiskAssessment,
    StrategyAnalysis,
)
from src.ai.provider import LLMProvider
from src.pipelines.cfo_ai_pipeline import (
    build_cfo_ai_orchestrator,
)
from src.planning.dependency_resolver import (
    CANONICAL_AGENT_ORDER,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class RecordingPipelineProvider(LLMProvider):
    """Fake provider that records requests without network calls."""

    def __init__(self) -> None:
        self.requests: list[AIRequest] = []

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.requests.append(request)

        return AITextResult(
            content="Fake response",
            model="fake-model",
            provider="fake-provider",
        )

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        payloads: dict[type[BaseModel], dict] = {
            FinancialExplanation: {
                "summary": "The ledger result is verified.",
                "key_points": [
                    "Debit equals credit.",
                ],
                "recommendations": [
                    "Continue the review process.",
                ],
            },
            ControllerReview: {
                "summary": "The Controller review is complete.",
                "control_findings": [
                    "The trial balance is balanced.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain supporting evidence.",
                ],
            },
            RiskAssessment: {
                "summary": "The current financial risk is low.",
                "risk_level": "LOW",
                "risk_findings": [
                    "No material imbalance was identified.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Continue monthly reconciliation.",
                ],
            },
            ForecastAnalysis: {
                "summary": "The expected outlook is stable.",
                "assumptions": [
                    "Verified activity remains stable.",
                ],
                "expected_scenario": [
                    "Liquidity remains positive.",
                ],
                "downside_risks": [
                    "Unexpected expense growth.",
                ],
                "recommendations": [
                    "Monitor monthly cash movement.",
                ],
            },
            StrategyAnalysis: {
                "summary": "Liquidity protection is the priority.",
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
                    "Cost control may limit short-term growth.",
                ],
            },
            ChiefCFOBrief: {
                "executive_summary": (
                    "The verified financial position is stable."
                ),
                "key_financial_signals": [
                    "Accounting records are balanced.",
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

        payload = payloads.get(output_schema)

        if payload is None:
            raise AssertionError(
                f"Unsupported schema: {output_schema}"
            )

        return output_schema.model_validate(payload)


def build_verified_initial_results() -> dict:
    """Return deterministic results required by AI adapters."""

    return {
        "general_ledger": {
            "journal_id": "JRN-001",
            "total_debit": "1000.00",
            "total_credit": "1000.00",
            "currency": "USD",
        },
        "controller": {
            "status": "APPROVED",
            "is_balanced": True,
        },
    }


def get_executed_ai_agents(context) -> list[str]:
    """Return dynamic AI agents that produced results."""

    return [
        agent_name
        for agent_name in CANONICAL_AGENT_ORDER
        if context.has_result(agent_name)
    ]


def test_real_general_ledger_request_executes_one_ai_agent():
    provider = RecordingPipelineProvider()

    orchestrator = build_cfo_ai_orchestrator(
        provider=provider,
    )

    user_request = (
        "\u0627\u0634\u0631\u062d "
        "\u0627\u0644\u0642\u064a\u062f "
        "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a"
    )

    context = orchestrator.run(
        user_request,
        initial_results={
            "general_ledger": (
                build_verified_initial_results()[
                    "general_ledger"
                ]
            ),
        },
    )

    assert get_executed_ai_agents(context) == [
        "general_ledger_ai",
    ]

    assert len(provider.requests) == 1
    assert provider.requests[0].user_input == user_request
    assert context.errors == []


def test_real_risk_request_executes_minimum_ai_agents():
    provider = RecordingPipelineProvider()

    orchestrator = build_cfo_ai_orchestrator(
        provider=provider,
    )

    user_request = (
        "\u062d\u0644\u0644 "
        "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 "
        "\u0648\u0627\u0644\u0631\u0642\u0627\u0628\u0629 "
        "\u0627\u0644\u062f\u0627\u062e\u0644\u064a\u0629"
    )

    context = orchestrator.run(
        user_request,
        metadata={
            "company_id": "COMPANY-001",
            "currency": "USD",
        },
        initial_results=build_verified_initial_results(),
    )

    assert get_executed_ai_agents(context) == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    ]

    assert len(provider.requests) == 3

    assert all(
        request.user_input == user_request
        for request in provider.requests
    )

    assert context.errors == []

    risk_result = context.get_result(
        "risk_ai"
    )

    assert risk_result["risk_level"] == "LOW"


def test_real_full_report_executes_all_ai_agents():
    provider = RecordingPipelineProvider()

    orchestrator = build_cfo_ai_orchestrator(
        provider=provider,
    )

    user_request = (
        "\u0627\u0639\u0637\u0646\u064a "
        "\u062a\u0642\u0631\u064a\u0631 CFO "
        "\u0643\u0627\u0645\u0644"
    )

    context = orchestrator.run(
        user_request,
        initial_results=build_verified_initial_results(),
    )

    assert get_executed_ai_agents(context) == list(
        CANONICAL_AGENT_ORDER
    )

    assert len(provider.requests) == 6
    assert context.errors == []

    chief_cfo_result = context.get_result(
        "chief_cfo_ai"
    )

    assert chief_cfo_result["executive_summary"] == (
        "The verified financial position is stable."
    )


def test_missing_verified_controller_data_blocks_dependents():
    provider = RecordingPipelineProvider()

    orchestrator = build_cfo_ai_orchestrator(
        provider=provider,
    )

    context = orchestrator.run(
        "\u062d\u0644\u0644 "
        "\u0627\u0644\u0645\u062e\u0627\u0637\u0631",
        initial_results={
            "general_ledger": {
                "journal_id": "JRN-001",
                "total_debit": "1000.00",
                "total_credit": "1000.00",
            },
        },
    )

    assert context.has_result(
        "general_ledger_ai"
    )

    assert not context.has_result(
        "controller_ai"
    )

    assert not context.has_result(
        "risk_ai"
    )

    assert len(provider.requests) == 1
    assert len(context.errors) == 2

    assert context.errors[0].agent_name == (
        "controller_ai"
    )

    assert context.errors[1].agent_name == (
        "risk_ai"
    )
