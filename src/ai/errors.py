"""Exceptions raised by the CFO.ai AI layer."""

from __future__ import annotations


class AIProviderError(RuntimeError):
    """Safe normalized error raised by an LLM provider."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)

        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable


class AIProviderResponseError(AIProviderError):
    """Raised when a provider returns an unusable response."""
