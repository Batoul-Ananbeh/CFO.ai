"""Routing logic for CFO.ai LangGraph workflows."""

from typing import Literal

from src.graphs.state import CFOGraphState
from src.schemas.enums import ControllerDecisionStatus


ControllerRoute = Literal[
    "approved",
    "approved_with_warnings",
    "requires_correction",
    "requires_human_approval",
    "blocked",
    "insufficient_data",
]


def route_controller_decision(state: CFOGraphState) -> ControllerRoute:
    """Route the graph according to the Controller Agent decision."""

    controller_result = state.get("controller_result")

    if controller_result is None:
        raise ValueError(
            "Controller result is missing from the graph state."
        )

    decision_status = controller_result.decision_status

    route_map: dict[ControllerDecisionStatus, ControllerRoute] = {
        ControllerDecisionStatus.APPROVED: "approved",
        ControllerDecisionStatus.APPROVED_WITH_WARNINGS:
            "approved_with_warnings",
        ControllerDecisionStatus.REQUIRES_CORRECTION:
            "requires_correction",
        ControllerDecisionStatus.REQUIRES_HUMAN_APPROVAL:
            "requires_human_approval",
        ControllerDecisionStatus.BLOCKED: "blocked",
        ControllerDecisionStatus.INSUFFICIENT_DATA:
            "insufficient_data",
    }

    try:
        return route_map[decision_status]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported Controller decision status: {decision_status}"
        ) from exc