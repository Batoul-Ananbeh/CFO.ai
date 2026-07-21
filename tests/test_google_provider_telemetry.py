"""Offline tests for Gemini response telemetry."""

from __future__ import annotations

from types import SimpleNamespace

from src.ai.context_utils import attach_ai_metadata
from src.ai.google_provider import GoogleGenAIProvider
from src.ai.models import AIRequest
from src.ai.outputs import FinancialExplanation
from src.ai.settings import AISettings


class FakeModels:
    def __init__(self, response) -> None:
        self.response = response

    def generate_content(self, **kwargs):
        del kwargs
        return self.response


class FakeClient:
    def __init__(self, response) -> None:
        self.models = FakeModels(response)


def create_settings() -> AISettings:
    return AISettings(
        provider="google",
        model="fake-gemini",
        temperature=0.0,
        api_key=None,
        timeout_ms=60_000,
        retry_attempts=4,
        max_output_tokens=2_048,
    )


def create_usage():
    return SimpleNamespace(
        prompt_token_count=100,
        candidates_token_count=40,
        total_token_count=140,
        cached_content_token_count=10,
        thoughts_token_count=5,
    )


def test_google_provider_collects_text_usage_metadata():
    response = SimpleNamespace(
        text="Verified financial explanation.",
        parsed=None,
        usage_metadata=create_usage(),
        response_id="response-001",
        model_version="fake-gemini-v1",
    )

    provider = GoogleGenAIProvider(
        settings=create_settings(),
        client=FakeClient(response),
    )

    result = provider.generate_text(
        AIRequest(
            instruction="Use verified data only.",
            user_input="Explain the result.",
            context={"currency": "USD"},
        )
    )

    assert result.metadata is not None
    assert result.metadata.response_id == "response-001"
    assert result.metadata.usage is not None
    assert result.metadata.usage.total_tokens == 140


def test_google_provider_collects_structured_usage_metadata():
    response = SimpleNamespace(
        text=None,
        parsed={
            "summary": "The entry is balanced.",
            "key_points": [
                "Debit equals credit.",
            ],
            "recommendations": [
                "Continue Controller review.",
            ],
        },
        usage_metadata=create_usage(),
        response_id="response-002",
        model_version="fake-gemini-v1",
    )

    provider = GoogleGenAIProvider(
        settings=create_settings(),
        client=FakeClient(response),
    )

    result = provider.generate_structured(
        request=AIRequest(
            instruction="Use verified data only.",
            user_input="Explain the result.",
            context={"currency": "USD"},
        ),
        output_schema=FinancialExplanation,
    )

    assert result.summary == "The entry is balanced."
    assert provider.last_call_metadata is not None
    assert (
        provider.last_call_metadata.usage.total_tokens
        == 140
    )


def test_metadata_can_be_attached_to_agent_result():
    response = SimpleNamespace(
        text="Verified response.",
        parsed=None,
        usage_metadata=create_usage(),
        response_id="response-003",
        model_version="fake-gemini-v1",
    )

    provider = GoogleGenAIProvider(
        settings=create_settings(),
        client=FakeClient(response),
    )

    provider.generate_text(
        AIRequest(
            instruction="Use verified data only.",
            user_input="Explain.",
            context={},
        )
    )

    payload = attach_ai_metadata(
        {
            "summary": "Completed.",
        },
        provider,
    )

    assert "_ai_metadata" in payload
    assert (
        payload["_ai_metadata"]["usage"]["total_tokens"]
        == 140
    )
