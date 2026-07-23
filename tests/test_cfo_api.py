"""HTTP API tests for CFO.ai."""

from __future__ import annotations

from typing import Any, TypeVar

from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.ai.errors import (
    AIProviderError,
    AIProviderResponseError,
)
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
from src.api.app import create_app
from src.application.factory import (
    build_cfo_application_service,
)


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FakeAPIProvider(LLMProvider):
    """Fake provider used by successful HTTP API tests."""

    def __init__(self) -> None:
        self.requests: list[AIRequest] = []

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.requests.append(request)

        return AITextResult(
            content="Fake API response",
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
                    "The journal entry is verified."
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
                    "The Controller review is complete."
                ),
                "control_findings": [
                    "The journal entry is balanced.",
                ],
                "required_corrections": [],
                "recommendations": [
                    "Retain supporting evidence.",
                ],
            },
            RiskAssessment: {
                "summary": (
                    "The current financial risk is low."
                ),
                "risk_level": "LOW",
                "risk_findings": [
                    "No accounting imbalance exists.",
                ],
                "missing_information": [],
                "recommended_controls": [
                    "Continue monthly reconciliation.",
                ],
            },
            ForecastAnalysis: {
                "summary": (
                    "The expected outlook is stable."
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
                    "Monitor cash movement.",
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
                    "Cost controls may limit growth.",
                ],
            },
            ChiefCFOBrief: {
                "executive_summary": (
                    "The verified financial position is stable."
                ),
                "key_financial_signals": [
                    "The journal entry was approved.",
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

        return output_schema.model_validate(
            payload
        )


class InvalidResponseAPIProvider(FakeAPIProvider):
    """Provider that simulates an unusable AI response."""

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        raise AIProviderResponseError(
            "The AI provider returned an unusable response.",
            provider="google",
            status_code=200,
            retryable=False,
        )


class UnavailableAPIProvider(FakeAPIProvider):
    """Provider that simulates temporary AI unavailability."""

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        raise AIProviderError(
            "The AI provider is temporarily unavailable.",
            provider="google",
            status_code=503,
            retryable=True,
        )


class InternalFailureAPIProvider(FakeAPIProvider):
    """Provider that simulates an unexpected internal failure."""

    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        self.requests.append(request)

        raise RuntimeError(
            "Unexpected provider adapter failure."
        )


def valid_transaction() -> dict[str, Any]:
    """Return a JSON-compatible valid transaction."""

    return {
        "transaction_id": "TXN-API-001",
        "accounting_period": "2026-07",
        "transaction_category": "CASH_SALE",
        "description": (
            "Cash sale processed through the HTTP API"
        ),
        "amount": {
            "amount": "2000.00",
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


def build_client_with_provider(
    provider: LLMProvider,
) -> TestClient:
    """Build an API client using the supplied AI provider."""

    service = build_cfo_application_service(
        provider=provider
    )

    app = create_app(
        service=service
    )

    return TestClient(app)


def build_test_client() -> tuple[
    TestClient,
    FakeAPIProvider,
]:
    """Build an API client with an offline successful provider."""

    provider = FakeAPIProvider()

    client = build_client_with_provider(
        provider
    )

    return client, provider


def single_agent_request() -> dict[str, Any]:
    """Return a request that executes only General Ledger AI."""

    return {
        "request": (
            "\u0627\u0634\u0631\u062d "
            "\u0627\u0644\u0642\u064a\u062f "
            "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a"
        ),
        "financial_input": valid_transaction(),
    }


def test_health_endpoint():
    client, _ = build_test_client()

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "CFO.ai",
        "api_version": "1.0.0",
    }


def test_agent_catalog_endpoint():
    client, _ = build_test_client()

    response = client.get(
        "/api/v1/agents"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 6

    assert [
        agent["name"]
        for agent in payload["agents"]
    ] == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
        "chief_cfo_ai",
    ]


def test_api_runs_dynamic_risk_analysis():
    client, provider = build_test_client()

    response = client.post(
        "/api/v1/analyses",
        json={
            "request": (
                "\u062d\u0644\u0644 "
                "\u0645\u062e\u0627\u0637\u0631 "
                "\u0647\u0630\u0647 "
                "\u0627\u0644\u0639\u0645\u0644\u064a\u0629"
            ),
            "financial_input": valid_transaction(),
            "metadata": {
                "correlation_id": (
                    "CORR-API-001"
                ),
                "company_id": "COMPANY-001",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "COMPLETED"

    assert payload["correlation_id"] == (
        "CORR-API-001"
    )

    assert payload["executed_agents"] == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    ]

    assert payload["final_agent"] == "risk_ai"

    assert payload["final_output"][
        "risk_level"
    ] == "LOW"

    assert len(provider.requests) == 3


def test_api_runs_complete_cfo_report():
    client, provider = build_test_client()

    response = client.post(
        "/api/v1/analyses",
        json={
            "request": (
                "\u0627\u0639\u0637\u0646\u064a "
                "\u062a\u0642\u0631\u064a\u0631 CFO "
                "\u0643\u0627\u0645\u0644"
            ),
            "financial_input": valid_transaction(),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "COMPLETED"
    assert len(payload["executed_agents"]) == 6
    assert len(provider.requests) == 6

    assert payload["final_agent"] == (
        "chief_cfo_ai"
    )

    assert payload["final_output"][
        "executive_summary"
    ] == (
        "The verified financial position is stable."
    )


def test_api_rejects_invalid_request_schema():
    client, provider = build_test_client()

    response = client.post(
        "/api/v1/analyses",
        json={
            "request": "Analyze this transaction",
        },
    )

    assert response.status_code == 422
    assert len(provider.requests) == 0

    detail = response.json()["detail"]

    assert any(
        error["loc"][-1] == "financial_input"
        for error in detail
    )


def test_api_returns_422_for_invalid_transaction():
    client, provider = build_test_client()

    transaction = valid_transaction()

    transaction["credit_account"] = {
        "account_code": "1100",
        "account_name": "Bank",
    }

    response = client.post(
        "/api/v1/analyses",
        json={
            "request": (
                "\u062d\u0644\u0644 "
                "\u0645\u062e\u0627\u0637\u0631 "
                "\u0627\u0644\u0639\u0645\u0644\u064a\u0629"
            ),
            "financial_input": transaction,
        },
    )

    assert response.status_code == 422

    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["executed_agents"] == []
    assert len(payload["errors"]) == 1

    error = payload["errors"][0]

    assert error["agent_name"] == (
        "deterministic_finance"
    )

    assert error["category"] == "VALIDATION"
    assert error["provider_status_code"] is None
    assert error["retryable"] is False

    assert len(provider.requests) == 0


def test_api_returns_502_for_invalid_provider_response():
    provider = InvalidResponseAPIProvider()

    client = build_client_with_provider(
        provider
    )

    response = client.post(
        "/api/v1/analyses",
        json=single_agent_request(),
    )

    assert response.status_code == 502

    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["executed_agents"] == []
    assert len(payload["errors"]) == 1

    error = payload["errors"][0]

    assert error["agent_name"] == (
        "general_ledger_ai"
    )

    assert error["category"] == (
        "AI_PROVIDER_RESPONSE"
    )

    assert error["provider_status_code"] == 200
    assert error["retryable"] is False

    assert len(provider.requests) == 1


def test_api_returns_503_when_provider_is_unavailable():
    provider = UnavailableAPIProvider()

    client = build_client_with_provider(
        provider
    )

    response = client.post(
        "/api/v1/analyses",
        json=single_agent_request(),
    )

    assert response.status_code == 503

    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["executed_agents"] == []
    assert len(payload["errors"]) == 1

    error = payload["errors"][0]

    assert error["agent_name"] == (
        "general_ledger_ai"
    )

    assert error["category"] == (
        "AI_PROVIDER_UNAVAILABLE"
    )

    assert error["provider_status_code"] == 503
    assert error["retryable"] is True

    assert len(provider.requests) == 1


def test_api_returns_500_for_unexpected_internal_error():
    provider = InternalFailureAPIProvider()

    client = build_client_with_provider(
        provider
    )

    response = client.post(
        "/api/v1/analyses",
        json=single_agent_request(),
    )

    assert response.status_code == 500

    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["executed_agents"] == []
    assert len(payload["errors"]) == 1

    error = payload["errors"][0]

    assert error["agent_name"] == (
        "general_ledger_ai"
    )

    assert error["category"] == "INTERNAL"
    assert error["provider_status_code"] is None
    assert error["retryable"] is False

    assert len(provider.requests) == 1