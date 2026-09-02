"""AI analysis layer for financial strategy recommendations."""

from __future__ import annotations

from typing import Any

from src.ai.financial_agent import FinancialAIAgent
from src.ai.outputs import StrategyAnalysis
from src.ai.provider import LLMProvider


class StrategyAIAgent(
    FinancialAIAgent[StrategyAnalysis]
):
    """
    Produce strategic recommendations from verified financial context.

    Every recommendation must remain connected to verified information.
    """

    agent_name = "strategy_ai_agent"
    prompt_name = "strategy"
    output_schema = StrategyAnalysis

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

    def recommend(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str = (
            "Create financial strategy recommendations from the "
            "verified context and explain benefits and trade-offs."
        ),
    ) -> StrategyAnalysis:
        """Generate structured strategic recommendations."""

        return self.analyze_verified_context(
            verified_context=verified_context,
            user_input=user_input,
        )