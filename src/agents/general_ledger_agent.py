"""General Ledger Agent implementation."""

from __future__ import annotations

from typing import Any

from src.agents.general_ledger_ai_agent import (
    GeneralLedgerAIAgent,
)
from src.agents.general_ledger_explanation import (
    explain_general_ledger_result,
)
from src.ai.outputs import FinancialExplanation
from src.engines.general_ledger_engine import (
    prepare_draft_journal_entry,
)
from src.schemas.general_ledger import (
    GeneralLedgerResult,
    LedgerTransactionInput,
)


class GeneralLedgerAgent:
    """
    Prepare draft journal entries using deterministic accounting rules.

    The deterministic engine remains responsible for accounting
    calculations. The optional AI layer only explains verified results.

    The Agent does not:
    - post journal entries
    - approve its own entries
    - execute payments
    """

    agent_name = "general_ledger_agent"

    def __init__(
        self,
        ai_agent: GeneralLedgerAIAgent | None = None,
    ) -> None:
        self.ai_agent = ai_agent

    def prepare_entry(
        self,
        input_data: LedgerTransactionInput,
        correlation_id: str,
    ) -> GeneralLedgerResult:
        """Prepare a draft journal entry for Controller review."""

        return prepare_draft_journal_entry(
            input_data=input_data,
            correlation_id=correlation_id,
        )

    def explain(
        self,
        result: GeneralLedgerResult,
    ) -> str:
        """
        Explain a GL result using the deterministic explanation layer.
        """

        return explain_general_ledger_result(result)

    def explain_with_ai(
        self,
        result: GeneralLedgerResult,
        user_input: str = (
            "Explain this General Ledger result and provide "
            "the important accounting points and recommendations."
        ),
    ) -> FinancialExplanation:
        """
        Explain a verified GL result through the optional AI layer.
        """

        if self.ai_agent is None:
            raise RuntimeError(
                "General Ledger AI Agent is not configured. "
                "Pass GeneralLedgerAIAgent when creating "
                "GeneralLedgerAgent."
            )

        result_context = self._serialize_result(result)

        return self.ai_agent.explain_verified_result(
            result_context=result_context,
            user_input=user_input,
        )

    @staticmethod
    def _serialize_result(
        result: GeneralLedgerResult,
    ) -> dict[str, Any]:
        """
        Convert a Pydantic result into JSON-compatible context.
        """

        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")

        raise TypeError(
            "GeneralLedgerResult must support model_dump()."
        )