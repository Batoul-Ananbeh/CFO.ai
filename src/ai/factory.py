"""Factory functions for AI providers."""

from __future__ import annotations

from src.ai.google_provider import GoogleGenAIProvider
from src.ai.provider import LLMProvider
from src.ai.settings import AISettings


def create_llm_provider(
    settings: AISettings | None = None,
) -> LLMProvider:
    """Create the configured LLM provider."""

    resolved_settings = settings or AISettings.from_env()

    if resolved_settings.provider == "google":
        return GoogleGenAIProvider(settings=resolved_settings)

    raise ValueError(
        f"Unsupported AI provider: "
        f"{resolved_settings.provider!r}"
    )