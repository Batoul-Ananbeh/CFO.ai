"""General Ledger Agent implementation."""

from __future__ import annotations

from src.agents.general_ledger_explanation import (
    explain_general_ledger_result,
)

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

    The Agent does not:
    - post journal entries
    - approve its own entries
    - execute payments
    """

    agent_name = "general_ledger_agent"

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
        """Explain the GL result without changing it."""

        return explain_general_ledger_result(result)