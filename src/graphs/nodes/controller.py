"""LangGraph node for the Financial Controller Agent."""

from collections.abc import Callable

from src.agents.controller_agent import FinancialControllerAgent
from src.graphs.state import CFOGraphState
from src.schemas.controller import ReportType, TrialBalanceInput


def create_controller_node(
    agent: FinancialControllerAgent,
) -> Callable[[CFOGraphState], dict]:
    """Create a Controller node using the supplied agent."""

    def node(state: CFOGraphState) -> dict:
        general_ledger_result = state["general_ledger_result"]
        journal = general_ledger_result.journal_entry

        if journal is None:
            raise ValueError(
                "General Ledger Agent did not produce a draft journal entry."
            )

        controller_input = TrialBalanceInput(
            report_id=journal.journal_id,
            accounting_period=journal.accounting_period,
            total_debit=journal.total_debit,
            total_credit=journal.total_credit,
        )

        result = agent.review(
            report_type=ReportType.JOURNAL_ENTRY,
            input_data=controller_input,
            correlation_id=state["correlation_id"],
        )

        completed_steps = list(state.get("completed_steps", []))
        completed_steps.append("controller")

        return {
            "controller_result": result,
            "current_step": "controller",
            "completed_steps": completed_steps,
            "final_status": str(result.decision_status.value),
        }

    return node


_default_controller_agent = FinancialControllerAgent()
controller_node = create_controller_node(
    _default_controller_agent
)
