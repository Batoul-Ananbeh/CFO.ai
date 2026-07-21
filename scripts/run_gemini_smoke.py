"""Run one real Gemini structured-output request."""

from __future__ import annotations

from src.agents.general_ledger_ai_agent import (
    GeneralLedgerAIAgent,
)
from src.ai.factory import create_llm_provider


def main() -> None:
    provider = create_llm_provider()

    agent = GeneralLedgerAIAgent(
        provider=provider,
    )

    result = agent.explain_verified_result(
        result_context={
            "journal_id": "JRN-SMOKE-001",
            "accounting_period": "2026-07",
            "currency": "USD",
            "total_debit": "1000.00",
            "total_credit": "1000.00",
            "status": "READY_FOR_CONTROLLER_REVIEW",
            "entries": [
                {
                    "account": "1100 Bank",
                    "debit": "1000.00",
                    "credit": "0.00",
                },
                {
                    "account": "4100 Sales Revenue",
                    "debit": "0.00",
                    "credit": "1000.00",
                },
            ],
        }
    )

    print()
    print("STRUCTURED RESULT")
    print(result.model_dump_json(indent=2))

    print()
    print("CALL METADATA")

    metadata = provider.last_call_metadata

    if metadata is None:
        print("No metadata returned.")
    else:
        print(metadata.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
