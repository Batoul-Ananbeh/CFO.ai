"""AI explanation layer for Financial Controller results."""

from __future__ import annotations

from typing import Any

from src.ai.financial_agent import FinancialAIAgent
from src.ai.outputs import ControllerReview
from src.ai.provider import LLMProvider


class ControllerAIAgent(
    FinancialAIAgent[ControllerReview]
):
    """
    Explain verified Controller findings.

    This agent does not approve transactions, post journal entries,
    or modify deterministic Controller decisions.
    """

    agent_name = "controller_ai_agent"
    prompt_name = "controller"
    output_schema = ControllerReview

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

    def review(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str = (
            "Explain the Controller review, identify control "
            "findings, required corrections, and recommendations."
        ),
    ) -> ControllerReview:
        """Generate a structured Controller review explanation."""

        return self.analyze_verified_context(
            verified_context=verified_context,
            user_input=user_input,
        )