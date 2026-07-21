"""AI explanation layer for verified financial forecasts."""

from __future__ import annotations

from typing import Any

from src.ai.financial_agent import FinancialAIAgent
from src.ai.outputs import ForecastAnalysis
from src.ai.provider import LLMProvider


class ForecastAIAgent(
    FinancialAIAgent[ForecastAnalysis]
):
    """
    Explain verified forecast outputs and their assumptions.

    This agent does not calculate unsupported projections or present
    estimates as confirmed financial facts.
    """

    agent_name = "forecast_ai_agent"
    prompt_name = "forecast"
    output_schema = ForecastAnalysis

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

    def analyze(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str = (
            "Explain the verified financial forecast, its "
            "assumptions, expected scenario, risks, and "
            "recommendations."
        ),
    ) -> ForecastAnalysis:
        """Generate a structured forecast analysis."""

        return self.analyze_verified_context(
            verified_context=verified_context,
            user_input=user_input,
        )