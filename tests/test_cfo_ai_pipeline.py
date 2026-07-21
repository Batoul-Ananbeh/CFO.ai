"""Integration test for the full CFO.ai AI pipeline."""

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
from src.orchestrator.dispatcher import Dispatcher
from src.orchestrator.orchestrator import Orchestrator
from src.orchestrator.registry import AgentRegistry
from src.pipelines.cfo_ai_pipeline import (
    CFOAIPlanner,
    configure_cfo_ai_registry,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakePipelineProvider(LLMProvider):
    """Fake provider used to test the complete pipeline offline."""

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
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
        payloads = {
            FinancialExplanation: {
                "summary": "The journal entry is balanced.",
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
                    "The trial balance is balanced.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain the supporting evidence.",
                ],
            },
            RiskAssessment: {
                "summary": "The current risk is low.",
                "risk_level": "LOW",
                "risk_findings": [
                    "No material imbalance was found.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Continue monthly reconciliation.",
                ],
            },
            ForecastAnalysis: {
                "summary": "The expected outlook is stable.",
                "assumptions": [
                    "Current verified activity continues.",
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
                    "Cost controls may limit short-term growth.",
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
                    "Continue monthly financial monitoring.",
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


def test_complete_cfo_ai_pipeline_runs_through_orchestrator():
    registry = AgentRegistry()

    configure_cfo_ai_registry(
        registry=registry,
        provider=FakePipelineProvider(),
    )

    orchestrator = Orchestrator(
        planner=CFOAIPlanner(),
        dispatcher=Dispatcher(registry),
    )

    context = orchestrator.run(
        "Analyze the verified financial position.",
        metadata={
            "company_id": "COMPANY-001",
            "accounting_period": "2026-07",
            "currency": "USD",
        },
        initial_results={
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
        },
    )

    expected_results = [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
        "chief_cfo_ai",
    ]

    for result_name in expected_results:
        assert context.has_result(result_name)

    assert context.errors == []

    chief_cfo_result = context.get_result(
        "chief_cfo_ai"
    )

    assert chief_cfo_result["executive_summary"] == (
        "The verified financial position is stable."
    )

    assert chief_cfo_result[
        "human_approvals_required"
    ] == [
        "Final financial approval.",
    ]
