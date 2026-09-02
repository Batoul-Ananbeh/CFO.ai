"""Tests for specialized CFO.ai intelligent agents."""

from __future__ import annotations

from typing import TypeVar

import pytest
from pydantic import BaseModel

from src.agents.chief_cfo_ai_agent import (
    ChiefCFOAIAgent,
)
from src.agents.controller_ai_agent import (
    ControllerAIAgent,
)
from src.agents.forecast_ai_agent import (
    ForecastAIAgent,
)
from src.agents.risk_ai_agent import (
    RiskAIAgent,
)
from src.agents.strategy_ai_agent import (
    StrategyAIAgent,
)
from src.ai.models import AIRequest, AITextResult
from src.ai.outputs import (
    ChiefCFOBrief,
    ControllerReview,
    ForecastAnalysis,
    RiskAssessment,
    StrategyAnalysis,
)
from src.ai.provider import LLMProvider


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakeSpecializedProvider(LLMProvider):
    """Fake provider that never sends network requests."""

    def __init__(self) -> None:
        self.last_request: AIRequest | None = None
        self.last_schema: type[BaseModel] | None = None

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.last_request = request

        return AITextResult(
            content="Fake specialized response",
            model="fake-model",
            provider="fake-provider",
        )

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.last_request = request
        self.last_schema = output_schema

        payloads: dict[type[BaseModel], dict] = {
            ControllerReview: {
                "summary": "The trial balance was reviewed.",
                "control_findings": [
                    "Total debit equals total credit.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain supporting documents.",
                ],
            },
            RiskAssessment: {
                "summary": "No critical risk was identified.",
                "risk_level": "LOW",
                "risk_findings": [
                    "The transaction is balanced.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Complete the Controller review.",
                ],
            },
            ForecastAnalysis: {
                "summary": "The forecast remains stable.",
                "assumptions": [
                    "Verified revenue remains unchanged.",
                ],
                "expected_scenario": [
                    "Cash remains positive.",
                ],
                "downside_risks": [
                    "Unexpected expense growth.",
                ],
                "recommendations": [
                    "Monitor monthly cash movement.",
                ],
            },
            StrategyAnalysis: {
                "summary": "Cash preservation is the priority.",
                "strategic_priorities": [
                    "Maintain adequate liquidity.",
                ],
                "recommended_actions": [
                    "Review nonessential expenses.",
                ],
                "expected_benefits": [
                    "Improved cash runway.",
                ],
                "risks_and_tradeoffs": [
                    "Cost reduction may slow growth.",
                ],
            },
            ChiefCFOBrief: {
                "executive_summary": (
                    "The verified financial position is stable."
                ),
                "key_financial_signals": [
                    "Balanced accounting records.",
                ],
                "critical_risks": [],
                "recommended_decisions": [
                    "Continue monthly financial monitoring.",
                ],
                "human_approvals_required": [
                    "Final Controller approval.",
                ],
            },
        }

        payload = payloads.get(output_schema)

        if payload is None:
            raise AssertionError(
                f"Unsupported test schema: {output_schema}"
            )

        return output_schema.model_validate(payload)


@pytest.mark.parametrize(
    (
        "agent_class",
        "method_name",
        "expected_schema",
        "prompt_text",
    ),
    [
        (
            ControllerAIAgent,
            "review",
            ControllerReview,
            "Financial Controller Agent",
        ),
        (
            RiskAIAgent,
            "assess",
            RiskAssessment,
            "Risk and Internal Audit Agent",
        ),
        (
            ForecastAIAgent,
            "analyze",
            ForecastAnalysis,
            "Financial Forecast Agent",
        ),
        (
            StrategyAIAgent,
            "recommend",
            StrategyAnalysis,
            "Financial Strategy Agent",
        ),
        (
            ChiefCFOAIAgent,
            "summarize",
            ChiefCFOBrief,
            "Chief CFO Agent",
        ),
    ],
)
def test_specialized_agent_returns_structured_output(
    agent_class,
    method_name: str,
    expected_schema: type[BaseModel],
    prompt_text: str,
):
    provider = FakeSpecializedProvider()

    agent = agent_class(
        provider=provider,
    )

    method = getattr(
        agent,
        method_name,
    )

    result = method(
        verified_context={
            "company_id": "COMPANY-001",
            "accounting_period": "2026-07",
            "currency": "USD",
            "source": "verified-test-context",
        }
    )

    assert isinstance(
        result,
        expected_schema,
    )

    assert provider.last_request is not None
    assert provider.last_schema is expected_schema

    assert (
        provider.last_request.context["company_id"]
        == "COMPANY-001"
    )

    assert (
        provider.last_request.context["currency"]
        == "USD"
    )

    assert (
        prompt_text
        in provider.last_request.instruction
    )