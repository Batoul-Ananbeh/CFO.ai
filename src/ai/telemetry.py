"""Telemetry models for CFO.ai language-model calls."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIUsageMetadata(BaseModel):
    """Token usage reported by the language-model provider."""

    model_config = ConfigDict(extra="ignore")

    prompt_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cached_tokens: int | None = Field(default=None, ge=0)
    thought_tokens: int | None = Field(default=None, ge=0)


class AICallMetadata(BaseModel):
    """Auditable metadata for one language-model call."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    response_id: str | None = None
    model_version: str | None = None
    usage: AIUsageMetadata | None = None
