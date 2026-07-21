"""Shared base implementation for specialized CFO.ai agents."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from src.ai.base_agent import BaseAIAgent
from src.ai.models import AIRequest
from src.ai.prompt_loader import load_agent_prompt
from src.ai.provider import LLMProvider


OutputModel = TypeVar(
    "OutputModel",
    bound=BaseModel,
)


class FinancialAIAgent(
    BaseAIAgent[OutputModel],
    Generic[OutputModel],
):
    """
    Shared implementation for CFO.ai specialized AI agents.

    Every specialized agent provides:

    - agent_name
    - prompt_name
    - output_schema

    The shared layer handles prompt loading, request construction,
    and structured-output generation.
    """

    agent_name: str
    prompt_name: str
    output_schema: type[OutputModel]

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

        if not self.prompt_name:
            raise ValueError(
                "Financial AI Agent must define prompt_name."
            )

        self.system_instruction = load_agent_prompt(
            self.prompt_name
        )

    def build_request(
        self,
        *,
        user_input: str,
        context: dict[str, Any],
    ) -> AIRequest:
        """Build the normalized provider request."""

        return AIRequest(
            instruction=self.system_instruction,
            user_input=user_input,
            context=context,
        )

    def analyze_verified_context(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str,
    ) -> OutputModel:
        """
        Analyze verified financial context and return structured output.
        """

        return self.generate_structured(
            user_input=user_input,
            context=verified_context,
            output_schema=self.output_schema,
        )