"""Tests for the unified deterministic and AI CFO runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

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
from src.runtime.hybrid_runtime import (
    UnifiedCFORuntime,
)
from src.runtime.models import HybridRuntimeStatus


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakeDeterministicRunner:
    """Return predefined verified financial results."""

    def __init__(
        self,
        results: Mapping[str, Any],
    ) -> None:
        self.results = dict(results)
        self.call_count = 0
        self.received_input: dict[str, Any] | None = None
        self.received_metadata: dict[str, Any] | None = None

    def run(
        self,
        *,
        financial_input: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.call_count += 1
        self.received_input = dict(financial_input)
        self.received_metadata = dict(metadata or {})

        return dict(self.results)


class FailingDeterministicRunner:
    """Raise an error from the verified finance layer."""

    def run(
        self,
        *,
        financial_input: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        del financial_input
        del metadata

        raise RuntimeError(
            "Verified accounting workflow failed."
        )


class FakeHybridProvider(LLMProvider):
    """Generate structured AI results without network requests."""

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

        payloads: dict[type[BaseModel], dict[str, Any]] = {
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
                "summary": "The current risk is low.",
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
                    "Cost controls may limit growth.",
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


def verified_results() -> dict[str, Any]:
    """Return valid deterministic GL and Controller outputs."""

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


def test_runtime_executes_general_ledger_request():
    deterministic_runner = FakeDeterministicRunner(
        verified_results()
    )

    provider = FakeHybridProvider()

    runtime = UnifiedCFORuntime(
        deterministic_runner=deterministic_runner,
        provider=provider,
    )

    user_request = (
        "\u0627\u0634\u0631\u062d "
        "\u0627\u0644\u0642\u064a\u062f "
        "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a"
    )

    result = runtime.run(
        user_request,
        financial_input={
            "transaction_id": "TXN-001",
            "amount": "1000.00",
            "currency": "USD",
        },
        metadata={
            "company_id": "COMPANY-001",
        },
    )

    assert result.status is HybridRuntimeStatus.COMPLETED

    assert result.execution_plan == (
        "general_ledger_ai",
    )

    assert result.executed_agents == (
        "general_ledger_ai",
    )

    assert len(provider.requests) == 1
    assert deterministic_runner.call_count == 1
    assert result.errors == ()


def test_runtime_executes_minimum_risk_agents():
    provider = FakeHybridProvider()

    runtime = UnifiedCFORuntime(
        deterministic_runner=FakeDeterministicRunner(
            verified_results()
        ),
        provider=provider,
    )

    result = runtime.run(
        "\u062d\u0644\u0644 "
        "\u0627\u0644\u0645\u062e\u0627\u0637\u0631",
        financial_input={
            "transaction_id": "TXN-002",
        },
    )

    assert result.status is HybridRuntimeStatus.COMPLETED

    assert result.executed_agents == (
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    )

    assert len(provider.requests) == 3

    assert result.ai_results[
        "risk_ai"
    ]["risk_level"] == "LOW"


def test_runtime_executes_complete_cfo_report():
    provider = FakeHybridProvider()

    runtime = UnifiedCFORuntime(
        deterministic_runner=FakeDeterministicRunner(
            verified_results()
        ),
        provider=provider,
    )

    result = runtime.run(
        "\u0627\u0639\u0637\u0646\u064a "
        "\u062a\u0642\u0631\u064a\u0631 CFO "
        "\u0643\u0627\u0645\u0644",
        financial_input={
            "company_id": "COMPANY-001",
        },
    )

    assert result.status is HybridRuntimeStatus.COMPLETED
    assert len(result.executed_agents) == 6
    assert len(provider.requests) == 6

    payload = result.to_dict()

    assert payload["status"] == "COMPLETED"

    assert payload["ai_results"][
        "chief_cfo_ai"
    ]["executive_summary"] == (
        "The verified financial position is stable."
    )


def test_runtime_returns_partial_when_verified_data_is_missing():
    provider = FakeHybridProvider()

    runtime = UnifiedCFORuntime(
        deterministic_runner=FakeDeterministicRunner(
            {
                "general_ledger": (
                    verified_results()[
                        "general_ledger"
                    ]
                ),
            }
        ),
        provider=provider,
    )

    result = runtime.run(
        "\u062d\u0644\u0644 "
        "\u0627\u0644\u0645\u062e\u0627\u0637\u0631",
        financial_input={
            "transaction_id": "TXN-003",
        },
    )

    assert result.status is HybridRuntimeStatus.PARTIAL

    assert result.executed_agents == (
        "general_ledger_ai",
    )

    assert len(result.errors) == 2


def test_runtime_handles_deterministic_failure():
    provider = FakeHybridProvider()

    runtime = UnifiedCFORuntime(
        deterministic_runner=FailingDeterministicRunner(),
        provider=provider,
    )

    result = runtime.run(
        "\u0627\u0639\u0637\u0646\u064a "
        "\u062a\u0642\u0631\u064a\u0631 CFO "
        "\u0643\u0627\u0645\u0644",
        financial_input={
            "company_id": "COMPANY-001",
        },
    )

    assert result.status is HybridRuntimeStatus.FAILED
    assert result.executed_agents == ()
    assert result.ai_results == {}
    assert len(provider.requests) == 0
    assert len(result.errors) == 1

    assert result.errors[0].agent_name == (
        "deterministic_finance"
    )
