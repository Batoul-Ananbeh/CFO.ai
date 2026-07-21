"""AI analysis layer for financial risk and internal audit."""

from __future__ import annotations

from typing import Any

from src.ai.financial_agent import FinancialAIAgent
from src.ai.outputs import RiskAssessment
from src.ai.provider import LLMProvider


class RiskAIAgent(
    FinancialAIAgent[RiskAssessment]
):
    """
    Analyze verified financial and internal-control risk information.

    This agent identifies risks but does not accuse individuals,
    execute controls, or change financial records.
    """

    agent_name = "risk_ai_agent"
    prompt_name = "risk"
    output_schema = RiskAssessment

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

    def assess(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str = (
            "Assess the verified financial and control risks, "
            "classify the risk level, and recommend controls."
        ),
    ) -> RiskAssessment:
        """Generate a structured risk assessment."""

        return self.analyze_verified_context(
            verified_context=verified_context,
            user_input=user_input,
        )