"""Terminal status nodes for CFO.ai LangGraph workflows."""

from src.graphs.state import CFOGraphState


def approved_node(state: CFOGraphState) -> dict:
    """Finalize an approved Controller decision."""

    return {
        "current_step": "approved",
        "final_status": "APPROVED",
        "summary": "The financial entry was approved by the Controller Agent.",
    }


def approved_with_warnings_node(state: CFOGraphState) -> dict:
    """Finalize an approved decision that contains warnings."""

    return {
        "current_step": "approved_with_warnings",
        "final_status": "APPROVED_WITH_WARNINGS",
        "summary": (
            "The financial entry was approved by the Controller Agent "
            "with warnings."
        ),
    }


def correction_node(state: CFOGraphState) -> dict:
    """Send the financial entry to the correction queue."""

    return {
        "current_step": "requires_correction",
        "final_status": "REQUIRES_CORRECTION",
        "summary": (
            "The financial entry requires correction before it can proceed."
        ),
    }


def human_approval_node(state: CFOGraphState) -> dict:
    """Send the financial entry to human approval."""

    return {
        "current_step": "requires_human_approval",
        "final_status": "REQUIRES_HUMAN_APPROVAL",
        "summary": (
            "The financial entry requires approval from a human reviewer."
        ),
    }


def blocked_node(state: CFOGraphState) -> dict:
    """Finalize a blocked financial entry."""

    return {
        "current_step": "blocked",
        "final_status": "BLOCKED",
        "summary": "The financial entry was blocked by the Controller Agent.",
    }


def insufficient_data_node(state: CFOGraphState) -> dict:
    """Finalize a financial entry with insufficient data."""

    return {
        "current_step": "insufficient_data",
        "final_status": "INSUFFICIENT_DATA",
        "summary": (
            "The financial entry cannot proceed because required data "
            "is missing."
        ),
    }