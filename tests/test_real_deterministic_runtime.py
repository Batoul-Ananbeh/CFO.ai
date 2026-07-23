"""End-to-end tests for the real deterministic CFO runtime."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, TypeVar

import pytest
from pydantic import BaseModel, ValidationError

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
from src.runtime.deterministic_runner import (
    GLControllerDeterministicRunner,
    build_gl_controller_cfo_runtime,
)
from src.runtime.models import HybridRuntimeStatus
from src.schemas.controller import ControllerResult
from src.schemas.general_ledger import GeneralLedgerResult


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakeEndToEndProvider(LLMProvider):
    """Fake AI provider that performs no network requests."""

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

        payloads: dict[
            type[BaseModel],
            dict[str, Any],
        ] = {
            FinancialExplanation: {
                "summary": (
                    "The journal entry is verified and balanced."
                ),
                "key_points": [
                    "Debit equals credit.",
                ],
                "recommendations": [
                    "Continue Controller review.",
                ],
            },
            ControllerReview: {
                "summary": (
                    "The Controller approved the verified entry."
                ),
                "control_findings": [
                    "No balance difference was found.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain supporting evidence.",
                ],
            },
            RiskAssessment: {
                "summary": (
                    "The verified transaction has low risk."
                ),
                "risk_level": "LOW",
                "risk_findings": [
                    "The accounting entry is balanced.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Continue monthly reconciliation.",
                ],
            },
            ForecastAnalysis: {
                "summary": (
                    "The verified outlook is stable."
                ),
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
                    "Monitor monthly cash movement.",
                ],
            },
            StrategyAnalysis: {
                "summary": (
                    "Liquidity protection is the priority."
                ),
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
                    "Cost control may reduce growth.",
                ],
            },
            ChiefCFOBrief: {
                "executive_summary": (
                    "The verified financial position is stable."
                ),
                "key_financial_signals": [
                    "The accounting entry was approved.",
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


def valid_transaction(
    *,
    currency: str = "USD",
) -> dict[str, Any]:
    """Return a valid raw transaction mapping."""

    return {
        "transaction_id": "TXN-REAL-RUNTIME-001",
        "accounting_period": "2026-07",
        "transaction_category": "CASH_SALE",
        "description": (
            "Cash sale processed through the real runtime"
        ),
        "amount": {
            "amount": Decimal("1000.00"),
            "currency": currency,
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


def test_real_runner_executes_langgraph_workflow():
    runner = GLControllerDeterministicRunner()

    results = runner.run(
        financial_input=valid_transaction(),
        metadata={
            "correlation_id": (
                "CORR-REAL-RUNTIME-001"
            ),
        },
    )

    general_ledger = results[
        "general_ledger"
    ]

    controller = results[
        "controller"
    ]

    workflow = results[
        "gl_controller_workflow"
    ]

    assert isinstance(
        general_ledger,
        GeneralLedgerResult,
    )

    assert isinstance(
        controller,
        ControllerResult,
    )

    assert (
        general_ledger.correlation_id
        == "CORR-REAL-RUNTIME-001"
    )

    assert (
        controller.correlation_id
        == "CORR-REAL-RUNTIME-001"
    )

    assert workflow["final_status"] == "APPROVED"

    assert (
        general_ledger.journal_entry
        is not None
    )

    assert (
        general_ledger
        .journal_entry
        .balance_difference
        .amount
        == Decimal("0")
    )


def test_real_runner_generates_correlation_id():
    runner = GLControllerDeterministicRunner()

    results = runner.run(
        financial_input=valid_transaction(
            currency="JOD"
        ),
    )

    correlation_id = results[
        "gl_controller_workflow"
    ]["correlation_id"]

    assert correlation_id.startswith(
        "CORR-"
    )

    assert (
        results["general_ledger"]
        .journal_entry
        .total_debit
        .currency
        == "JOD"
    )


def test_real_runner_rejects_invalid_transaction():
    runner = GLControllerDeterministicRunner()

    invalid_input = valid_transaction()

    invalid_input["credit_account"] = {
        "account_code": "1100",
        "account_name": "Bank",
    }

    with pytest.raises(
        ValidationError,
        match=(
            "debit and credit accounts "
            "must be different"
        ),
    ):
        runner.run(
            financial_input=invalid_input,
        )


def test_real_runtime_runs_deterministic_and_risk_ai():
    provider = FakeEndToEndProvider()

    runtime = build_gl_controller_cfo_runtime(
        provider=provider,
    )

    user_request = (
        "\u062d\u0644\u0644 "
        "\u0645\u062e\u0627\u0637\u0631 "
        "\u0647\u0630\u0647 "
        "\u0627\u0644\u0639\u0645\u0644\u064a\u0629"
    )

    result = runtime.run(
        user_request,
        financial_input=valid_transaction(),
        metadata={
            "correlation_id": (
                "CORR-END-TO-END-001"
            ),
            "company_id": "COMPANY-001",
        },
    )

    assert result.status is (
        HybridRuntimeStatus.COMPLETED
    )

    assert result.executed_agents == (
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    )

    assert len(provider.requests) == 3

    assert isinstance(
        result.verified_results[
            "general_ledger"
        ],
        GeneralLedgerResult,
    )

    assert isinstance(
        result.verified_results[
            "controller"
        ],
        ControllerResult,
    )

    assert (
        result.verified_results[
            "gl_controller_workflow"
        ]["final_status"]
        == "APPROVED"
    )

    assert (
        result.ai_results[
            "risk_ai"
        ]["risk_level"]
        == "LOW"
    )

    assert result.errors == ()


def test_real_runtime_result_is_api_serializable():
    provider = FakeEndToEndProvider()

    runtime = build_gl_controller_cfo_runtime(
        provider=provider,
    )

    result = runtime.run(
        "\u0627\u0634\u0631\u062d "
        "\u0627\u0644\u0642\u064a\u062f "
        "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a",
        financial_input=valid_transaction(
            currency="EUR"
        ),
    )

    payload = result.to_dict()

    assert payload["status"] == "COMPLETED"

    assert isinstance(
        payload["verified_results"][
            "general_ledger"
        ],
        dict,
    )

    assert isinstance(
        payload["verified_results"][
            "controller"
        ],
        dict,
    )

    journal_entry = payload[
        "verified_results"
    ]["general_ledger"]["journal_entry"]

    assert (
        journal_entry["total_debit"]["currency"]
        == "EUR"
    )

    assert payload["executed_agents"] == [
        "general_ledger_ai",
    ]
