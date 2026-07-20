"""Tests for CFO.ai LangGraph routing logic."""

import pytest

from src.graphs.router import route_controller_decision
from src.schemas.enums import ControllerDecisionStatus


class FakeControllerResult:
    """Minimal Controller result used to test graph routing."""

    def __init__(
        self,
        decision_status: ControllerDecisionStatus,
    ) -> None:
        self.decision_status = decision_status


@pytest.mark.parametrize(
    ("decision_status", "expected_route"),
    [
        (
            ControllerDecisionStatus.APPROVED,
            "approved",
        ),
        (
            ControllerDecisionStatus.APPROVED_WITH_WARNINGS,
            "approved_with_warnings",
        ),
        (
            ControllerDecisionStatus.REQUIRES_CORRECTION,
            "requires_correction",
        ),
        (
            ControllerDecisionStatus.REQUIRES_HUMAN_APPROVAL,
            "requires_human_approval",
        ),
        (
            ControllerDecisionStatus.BLOCKED,
            "blocked",
        ),
        (
            ControllerDecisionStatus.INSUFFICIENT_DATA,
            "insufficient_data",
        ),
    ],
)
def test_route_controller_decision(
    decision_status: ControllerDecisionStatus,
    expected_route: str,
) -> None:
    state = {
        "controller_result": FakeControllerResult(
            decision_status=decision_status,
        )
    }

    assert route_controller_decision(state) == expected_route


def test_route_controller_decision_requires_result() -> None:
    with pytest.raises(
        ValueError,
        match="Controller result is missing",
    ):
        route_controller_decision({})