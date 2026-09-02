"""Executive AI layer for the Chief CFO Agent."""

from __future__ import annotations

from typing import Any

from src.ai.financial_agent import FinancialAIAgent
from src.ai.outputs import ChiefCFOBrief
from src.ai.provider import LLMProvider


class ChiefCFOAIAgent(
    FinancialAIAgent[ChiefCFOBrief]
):
    """
    Combine verified outputs from specialized agents into an
    executive financial brief.

    This agent does not replace deterministic engines or execute
    financial actions.
    """

    agent_name = "chief_cfo_ai_agent"
    prompt_name = "chief_cfo"
    output_schema = ChiefCFOBrief

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        super().__init__(provider=provider)

    def summarize(
        self,
        *,
        verified_context: dict[str, Any],
        user_input: str = (
            "Create an executive CFO brief from the verified "
            "specialized-agent results, including risks, decisions, "
            "and required human approvals."
        ),
    ) -> ChiefCFOBrief:
        """Generate a structured executive CFO brief."""

        return self.analyze_verified_context(
            verified_context=verified_context,
            user_input=user_input,
        )