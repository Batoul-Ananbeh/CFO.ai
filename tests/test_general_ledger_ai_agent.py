"""Tests for the General Ledger AI explanation layer."""

from __future__ import annotations

from typing import TypeVar

import pytest
from pydantic import BaseModel

from src.agents.general_ledger_ai_agent import (
    GeneralLedgerAIAgent,
)
from src.ai.models import AIRequest, AITextResult
from src.ai.outputs import FinancialExplanation
from src.ai.prompt_loader import (
    clear_prompt_cache,
    load_agent_prompt,
    load_prompt,
)
from src.ai.provider import LLMProvider


OutputModel = TypeVar("OutputModel", bound=BaseModel)


class FakeLLMProvider(LLMProvider):
    """Fake provider that performs no network requests."""

    def __init__(self) -> None:
        self.last_request: AIRequest | None = None

    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        self.last_request = request

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
        self.last_request = request

        return output_schema.model_validate(
            {
                "summary": (
                    "The journal entry is ready for Controller review."
                ),
                "key_points": [
                    "The result was generated from verified context.",
                    "The AI layer did not modify the accounting entry.",
                ],
                "recommendations": [
                    "Review supporting documentation.",
                ],
            }
        )


def test_prompt_loader_loads_general_ledger_prompt():
    clear_prompt_cache()

    prompt = load_prompt("general_ledger")

    assert "General Ledger Explanation Agent" in prompt


def test_agent_prompt_contains_base_and_specific_rules():
    clear_prompt_cache()

    prompt = load_agent_prompt("general_ledger")

    assert "Never invent balances" in prompt
    assert "General Ledger Explanation Agent" in prompt


def test_general_ledger_ai_agent_returns_structured_output():
    provider = FakeLLMProvider()
    agent = GeneralLedgerAIAgent(provider=provider)

    result = agent.explain_verified_result(
        result_context={
            "journal_id": "JRN-001",
            "currency": "USD",
            "total_debit": "1000.00",
            "total_credit": "1000.00",
        }
    )

    assert isinstance(result, FinancialExplanation)

    assert result.summary == (
        "The journal entry is ready for Controller review."
    )

    assert provider.last_request is not None

    assert provider.last_request.context["journal_id"] == "JRN-001"
    assert provider.last_request.context["currency"] == "USD"

    assert (
        "General Ledger Explanation Agent"
        in provider.last_request.instruction
    )


def test_prompt_loader_rejects_invalid_file_names():
    with pytest.raises(ValueError):
        load_prompt("../secret")