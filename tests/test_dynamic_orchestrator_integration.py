"""Integration tests for dynamic CFO orchestration."""

from __future__ import annotations

from typing import Any

import pytest

from src.orchestrator.context import ExecutionContext
from src.orchestrator.factory import (
    build_dynamic_orchestrator,
)
from src.orchestrator.registry import AgentRegistry
from src.planning.dependency_resolver import (
    AGENT_DEPENDENCIES,
    CANONICAL_AGENT_ORDER,
)


class RecordingAgent:
    """Agent test double that records execution order."""

    def __init__(
        self,
        *,
        name: str,
        execution_order: list[str],
    ) -> None:
        self.name = name
        self.execution_order = execution_order
        self.execution_count = 0

    def execute(
        self,
        *,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Record execution and return an auditable result."""

        self.execution_count += 1
        self.execution_order.append(self.name)

        return {
            "agent_name": self.name,
            "request": context.request,
            "available_prior_results": tuple(
                context.results.keys()
            ),
            "status": "completed",
        }


def build_complete_registry(
    execution_order: list[str],
) -> AgentRegistry:
    """Create a registry containing all dynamic CFO agents."""

    registry = AgentRegistry()

    for agent_name in CANONICAL_AGENT_ORDER:
        registry.register(
            name=agent_name,
            agent=RecordingAgent(
                name=agent_name,
                execution_order=execution_order,
            ),
            required_inputs=set(
                AGENT_DEPENDENCIES[agent_name]
            ),
            capabilities={
                agent_name,
            },
        )

    return registry


def test_general_ledger_request_executes_one_agent():
    execution_order: list[str] = []

    registry = build_complete_registry(
        execution_order
    )

    orchestrator = build_dynamic_orchestrator(
        registry=registry
    )

    result = orchestrator.run(
        "\u0627\u0634\u0631\u062d "
        "\u0627\u0644\u0642\u064a\u062f "
        "\u0627\u0644\u0645\u062d\u0627\u0633\u0628\u064a"
    )

    assert execution_order == [
        "general_ledger_ai",
    ]

    assert list(result.results) == [
        "general_ledger_ai",
    ]

    assert result.errors == []


def test_risk_request_executes_only_required_agents():
    execution_order: list[str] = []

    registry = build_complete_registry(
        execution_order
    )

    orchestrator = build_dynamic_orchestrator(
        registry=registry
    )

    result = orchestrator.run(
        "\u062d\u0644\u0644 "
        "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 "
        "\u0648\u0627\u0644\u0631\u0642\u0627\u0628\u0629 "
        "\u0627\u0644\u062f\u0627\u062e\u0644\u064a\u0629"
    )

    expected_agents = [
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
    ]

    assert execution_order == expected_agents
    assert list(result.results) == expected_agents
    assert result.errors == []

    controller_result = result.get_result(
        "controller_ai"
    )

    assert controller_result[
        "available_prior_results"
    ] == (
        "general_ledger_ai",
    )

    risk_result = result.get_result(
        "risk_ai"
    )

    assert risk_result[
        "available_prior_results"
    ] == (
        "general_ledger_ai",
        "controller_ai",
    )


def test_full_cfo_report_executes_all_agents():
    execution_order: list[str] = []

    registry = build_complete_registry(
        execution_order
    )

    orchestrator = build_dynamic_orchestrator(
        registry=registry
    )

    result = orchestrator.run(
        "\u0627\u0639\u0637\u0646\u064a "
        "\u062a\u0642\u0631\u064a\u0631 CFO "
        "\u0643\u0627\u0645\u0644"
    )

    expected_agents = list(
        CANONICAL_AGENT_ORDER
    )

    assert execution_order == expected_agents
    assert list(result.results) == expected_agents
    assert result.errors == []

    chief_cfo_result = result.get_result(
        "chief_cfo_ai"
    )

    assert chief_cfo_result[
        "available_prior_results"
    ] == tuple(
        CANONICAL_AGENT_ORDER[:-1]
    )


def test_factory_rejects_incomplete_registry():
    registry = AgentRegistry()

    registry.register(
        name="general_ledger_ai",
        agent=RecordingAgent(
            name="general_ledger_ai",
            execution_order=[],
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Dynamic CFO registry is missing "
            "required agents"
        ),
    ):
        build_dynamic_orchestrator(
            registry=registry
        )
