"""Shared models for AI requests and responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.ai.telemetry import AICallMetadata


class AIRequest(BaseModel):
    """Normalized request passed to an AI agent."""

    model_config = ConfigDict(extra="forbid")

    instruction: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class AITextResult(BaseModel):
    """Normalized text result returned by an LLM provider."""

    model_config = ConfigDict(extra="forbid")

    content: str
    model: str
    provider: str
    metadata: AICallMetadata | None = None
