"""AI explanation layer for General Ledger results."""

from __future__ import annotations

from typing import Any

from src.ai.base_agent import BaseAIAgent
from src.ai.models import AIRequest
from src.ai.outputs import FinancialExplanation
from src.ai.prompt_loader import load_agent_prompt
from src.ai.provider import LLMProvider


class GeneralLedgerAIAgent(
    BaseAIAgent[FinancialExplanation]
):
    """
    Explain verified General Ledger results using an LLM.

    This agent does not calculate, modify, approve, or post
    journal entries.
    """

    agent_name = "general_ledger_ai_agent"

    def __init__(self, provider: LLMProvider) -> None:
        super().__init__(provider=provider)

        self.system_instruction = load_agent_prompt(
            "general_ledger"
        )

    def build_request(
        self,
        *,
        user_input: str,
        context: dict[str, Any],
    ) -> AIRequest:
        """
        Build a normalized request for the configured LLM provider.
        """

        return AIRequest(
            instruction=self.system_instruction,
            user_input=user_input,
            context=context,
        )

    def explain_verified_result(
        self,
        *,
        result_context: dict[str, Any],
        user_input: str = (
            "Explain this General Ledger result and provide "
            "the important accounting points and recommendations."
        ),
    ) -> FinancialExplanation:
        """
        Generate a structured explanation for a verified GL result.
        """

        return self.generate_structured(
            user_input=user_input,
            context=result_context,
            output_schema=FinancialExplanation,
        )