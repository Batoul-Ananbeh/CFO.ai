"""LangGraph node for the General Ledger Agent."""

from collections.abc import Callable

from src.agents.general_ledger_agent import GeneralLedgerAgent
from src.graphs.state import CFOGraphState


def create_general_ledger_node(
    agent: GeneralLedgerAgent,
) -> Callable[[CFOGraphState], dict]:
    """Create a General Ledger node using the supplied agent."""

    def node(state: CFOGraphState) -> dict:
        result = agent.prepare_entry(
            input_data=state["input_data"],
            correlation_id=state["correlation_id"],
        )

        completed_steps = list(state.get("completed_steps", []))
        completed_steps.append("general_ledger")

        return {
            "general_ledger_result": result,
            "current_step": "general_ledger",
            "completed_steps": completed_steps,
        }

    return node


_default_general_ledger_agent = GeneralLedgerAgent()
general_ledger_node = create_general_ledger_node(
    _default_general_ledger_agent
)