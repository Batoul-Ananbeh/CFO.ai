"""LLM provider abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from src.ai.models import AIRequest, AITextResult
from src.ai.telemetry import AICallMetadata


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class LLMProvider(ABC):
    """Contract implemented by every supported LLM provider."""

    @property
    def last_call_metadata(
        self,
    ) -> AICallMetadata | None:
        """
        Return metadata from the latest provider call.

        Providers that do not collect metadata may return None.
        """

        return None

    @abstractmethod
    def generate_text(
        self,
        request: AIRequest,
    ) -> AITextResult:
        """Generate a plain text result."""

    @abstractmethod
    def generate_structured(
        self,
        request: AIRequest,
        output_schema: type[OutputModel],
    ) -> OutputModel:
        """Generate and validate a structured result."""
