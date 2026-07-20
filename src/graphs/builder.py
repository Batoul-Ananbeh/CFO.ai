"""Build the CFO.ai LangGraph workflows."""

from langgraph.graph import END, START, StateGraph

from src.agents.controller_agent import FinancialControllerAgent
from src.agents.general_ledger_agent import GeneralLedgerAgent
from src.graphs.nodes.controller import create_controller_node
from src.graphs.nodes.general_ledger import create_general_ledger_node
from src.graphs.nodes.status import (
    approved_node,
    approved_with_warnings_node,
    blocked_node,
    correction_node,
    human_approval_node,
    insufficient_data_node,
)
from src.graphs.router import route_controller_decision
from src.graphs.state import CFOGraphState


def build_gl_controller_graph(
    gl_agent: GeneralLedgerAgent | None = None,
    controller_agent: FinancialControllerAgent | None = None,
):
    """Build and compile the General Ledger to Controller graph."""

    resolved_gl_agent = gl_agent or GeneralLedgerAgent()
    resolved_controller_agent = (
        controller_agent or FinancialControllerAgent()
    )

    graph_builder = StateGraph(CFOGraphState)

    graph_builder.add_node(
        "general_ledger",
        create_general_ledger_node(resolved_gl_agent),
    )

    graph_builder.add_node(
        "controller",
        create_controller_node(resolved_controller_agent),
    )

    graph_builder.add_node(
        "approved",
        approved_node,
    )

    graph_builder.add_node(
        "approved_with_warnings",
        approved_with_warnings_node,
    )

    graph_builder.add_node(
        "requires_correction",
        correction_node,
    )

    graph_builder.add_node(
        "requires_human_approval",
        human_approval_node,
    )

    graph_builder.add_node(
        "blocked",
        blocked_node,
    )

    graph_builder.add_node(
        "insufficient_data",
        insufficient_data_node,
    )

    graph_builder.add_edge(
        START,
        "general_ledger",
    )

    graph_builder.add_edge(
        "general_ledger",
        "controller",
    )

    graph_builder.add_conditional_edges(
        "controller",
        route_controller_decision,
        {
            "approved": "approved",
            "approved_with_warnings": "approved_with_warnings",
            "requires_correction": "requires_correction",
            "requires_human_approval": "requires_human_approval",
            "blocked": "blocked",
            "insufficient_data": "insufficient_data",
        },
    )

    graph_builder.add_edge(
        "approved",
        END,
    )

    graph_builder.add_edge(
        "approved_with_warnings",
        END,
    )

    graph_builder.add_edge(
        "requires_correction",
        END,
    )

    graph_builder.add_edge(
        "requires_human_approval",
        END,
    )

    graph_builder.add_edge(
        "blocked",
        END,
    )

    graph_builder.add_edge(
        "insufficient_data",
        END,
    )

    return graph_builder.compile()