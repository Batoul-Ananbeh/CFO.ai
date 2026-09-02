"""Tests for the CFO.ai dynamic planning engine."""

from __future__ import annotations

import pytest

from src.planning.dependency_resolver import (
    AgentDependencyResolver,
)
from src.planning.dynamic_planner import (
    DynamicCFOPlanner,
)
from src.planning.intents import FinancialIntent


@pytest.mark.parametrize(
    ("user_request", "expected_plan"),
    [
        (
            "اشرح القيد المحاسبي",
            [
                "general_ledger_ai",
            ],
        ),
        (
            "راجع القيد المحاسبي",
            [
                "general_ledger_ai",
                "controller_ai",
            ],
        ),
        (
            "حلل المخاطر والرقابة الداخلية",
            [
                "general_ledger_ai",
                "controller_ai",
                "risk_ai",
            ],
        ),
        (
            "اعطني توقع التدفق النقدي",
            [
                "general_ledger_ai",
                "controller_ai",
                "risk_ai",
                "forecast_ai",
            ],
        ),
        (
            "Create a financial strategy",
            [
                "general_ledger_ai",
                "controller_ai",
                "risk_ai",
                "forecast_ai",
                "strategy_ai",
            ],
        ),
        (
            "اعطني تقرير CFO كامل",
            [
                "general_ledger_ai",
                "controller_ai",
                "risk_ai",
                "forecast_ai",
                "strategy_ai",
                "chief_cfo_ai",
            ],
        ),
    ],
)
def test_dynamic_planner_builds_minimum_valid_plan(
    user_request: str,
    expected_plan: list[str],
):
    planner = DynamicCFOPlanner()

    assert planner.plan(user_request) == expected_plan


def test_dynamic_planner_combines_multiple_intents():
    planner = DynamicCFOPlanner()

    plan = planner.plan(
        "راجع القيد ثم حلل المخاطر"
    )

    assert plan == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    ]

    assert planner.last_plan_result is not None

    assert set(
        planner.last_plan_result.detected_intents
    ) == {
        FinancialIntent.CONTROLLER_REVIEW,
        FinancialIntent.RISK_ANALYSIS,
    }


def test_unknown_request_uses_complete_cfo_plan():
    planner = DynamicCFOPlanner()

    plan = planner.plan(
        "ساعدني في فهم وضعي"
    )

    assert plan == [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
        "chief_cfo_ai",
    ]


def test_dependency_resolver_rejects_unknown_agent():
    resolver = AgentDependencyResolver()

    with pytest.raises(KeyError):
        resolver.resolve_agents(
            ["unknown_agent"]
        )