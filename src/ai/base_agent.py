"""Base class for CFO.ai intelligent agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from src.ai.models import AIRequest, AITextResult
from src.ai.provider import LLMProvider


OutputModel = TypeVar("OutputModel", bound=BaseModel)


class BaseAIAgent(ABC, Generic[OutputModel]):
    """
    Base class for agents that use an external language model.

    Deterministic accounting calculations must remain outside the LLM.
    The LLM is used for explanation, classification, reasoning, and
    recommendation generation over verified inputs.
    """

    agent_name: str
    system_instruction: str

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    @abstractmethod
    def build_request(
        self,
        *,
        user_input: str,
        context: dict[str, Any],
    ) -> AIRequest:
        """Build the normalized request sent to the provider."""

    def generate_text(
        self,
        *,
        user_input: str,
        context: dict[str, Any],
    ) -> AITextResult:
        request = self.build_request(
            user_input=user_input,
            context=context,
        )

        return self.provider.generate_text(request)

    def generate_structured(
        self,
        *,
        user_input: str,
        context: dict[str, Any],
        output_schema: type[OutputModel],
    ) -> OutputModel:
        request = self.build_request(
            user_input=user_input,
            context=context,
        )

        return self.provider.generate_structured(
            request=request,
            output_schema=output_schema,
        )