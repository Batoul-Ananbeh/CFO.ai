"""Tests for the CFO.ai orchestrator dispatcher."""

from __future__ import annotations

from typing import Any

import pytest

from src.orchestrator.context import ExecutionContext
from src.orchestrator.dispatcher import Dispatcher
from src.orchestrator.registry import AgentRegistry


class FakeAgent:
    """Simple test agent that returns a predefined result."""

    def __init__(self, result: Any) -> None:
        self.result = result
        self.execution_count = 0
        self.received_context: ExecutionContext | None = None

    def execute(
        self,
        *,
        context: ExecutionContext,
    ) -> Any:
        """Execute the test agent."""

        self.execution_count += 1
        self.received_context = context

        return self.result


class OrderedFakeAgent:
    """Test agent that records its execution order."""

    def __init__(
        self,
        *,
        name: str,
        execution_order: list[str],
        result: Any,
    ) -> None:
        self.name = name
        self.execution_order = execution_order
        self.result = result

    def execute(
        self,
        *,
        context: ExecutionContext,
    ) -> Any:
        """Record execution order and return the configured result."""

        self.execution_order.append(self.name)

        return self.result


class InvalidAgent:
    """Agent that intentionally does not implement execute()."""


def register_agent(
    registry: AgentRegistry,
    *,
    name: str,
    agent: Any,
    required_inputs: set[str] | None = None,
) -> None:
    """Register an agent for dispatcher tests."""

    registry.register(
        name=name,
        agent=agent,
        required_inputs=required_inputs,
    )


def test_dispatch_rejects_empty_plan() -> None:
    registry = AgentRegistry()
    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Generate a financial report.",
    )

    with pytest.raises(
        ValueError,
        match="Execution plan cannot be empty",
    ):
        dispatcher.dispatch(
            [],
            context,
        )


def test_dispatch_executes_registered_agent() -> None:
    registry = AgentRegistry()

    agent = FakeAgent(
        result={
            "status": "completed",
        },
    )

    register_agent(
        registry,
        name="controller",
        agent=agent,
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Generate a financial report.",
    )

    result_context = dispatcher.dispatch(
        ["controller"],
        context,
    )

    assert result_context is context
    assert agent.execution_count == 1
    assert agent.received_context is context

    assert context.get_result("controller") == {
        "status": "completed",
    }

    assert context.errors == []


def test_dispatch_executes_agents_in_plan_order() -> None:
    registry = AgentRegistry()
    execution_order: list[str] = []

    controller = OrderedFakeAgent(
        name="controller",
        execution_order=execution_order,
        result="controller-result",
    )

    reporting = OrderedFakeAgent(
        name="reporting",
        execution_order=execution_order,
        result="reporting-result",
    )

    register_agent(
        registry,
        name="controller",
        agent=controller,
    )

    register_agent(
        registry,
        name="reporting",
        agent=reporting,
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Generate a financial report.",
    )

    result_context = dispatcher.dispatch(
        ["controller", "reporting"],
        context,
    )

    assert result_context is context

    assert execution_order == [
        "controller",
        "reporting",
    ]

    assert context.get_result("controller") == "controller-result"
    assert context.get_result("reporting") == "reporting-result"
    assert context.errors == []


def test_required_input_can_come_from_context_field() -> None:
    registry = AgentRegistry()
    agent = FakeAgent(result="completed")

    register_agent(
        registry,
        name="controller",
        agent=agent,
        required_inputs={"request"},
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Review the company ledger.",
    )

    result_context = dispatcher.dispatch(
        ["controller"],
        context,
    )

    assert result_context is context
    assert agent.execution_count == 1
    assert context.get_result("controller") == "completed"
    assert context.errors == []


def test_required_input_can_come_from_metadata() -> None:
    registry = AgentRegistry()
    agent = FakeAgent(result="completed")

    register_agent(
        registry,
        name="controller",
        agent=agent,
        required_inputs={"company_id"},
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Review the company ledger.",
        metadata={
            "company_id": "company-001",
        },
    )

    result_context = dispatcher.dispatch(
        ["controller"],
        context,
    )

    assert result_context is context
    assert agent.execution_count == 1
    assert context.get_result("controller") == "completed"
    assert context.errors == []


def test_required_input_can_come_from_previous_results() -> None:
    registry = AgentRegistry()

    controller = FakeAgent(
        result={
            "financial_data": "prepared",
        },
    )

    reporting = FakeAgent(
        result="report-created",
    )

    register_agent(
        registry,
        name="controller",
        agent=controller,
    )

    register_agent(
        registry,
        name="reporting",
        agent=reporting,
        required_inputs={"controller"},
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Generate a financial report.",
    )

    result_context = dispatcher.dispatch(
        ["controller", "reporting"],
        context,
    )

    assert result_context is context

    assert controller.execution_count == 1
    assert reporting.execution_count == 1

    assert context.get_result("controller") == {
        "financial_data": "prepared",
    }

    assert context.get_result("reporting") == "report-created"
    assert context.errors == []


def test_dispatch_records_missing_required_inputs() -> None:
    registry = AgentRegistry()
    agent = FakeAgent(result="done")

    register_agent(
        registry,
        name="controller",
        agent=agent,
        required_inputs={
            "company_id",
            "general_ledger",
        },
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Review the ledger.",
    )

    result_context = dispatcher.dispatch(
        ["controller"],
        context,
    )

    assert result_context is context
    assert agent.execution_count == 0
    assert not context.has_result("controller")
    assert len(context.errors) == 1

    error = context.errors[0]

    assert error.agent_name == "controller"
    assert error.exception_type == "ValueError"

    assert error.message == (
        "Agent 'controller' is missing required inputs: "
        "company_id, general_ledger."
    )


def test_dispatch_records_agent_without_execute_method() -> None:
    registry = AgentRegistry()

    register_agent(
        registry,
        name="invalid_agent",
        agent=InvalidAgent(),
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Run invalid agent.",
    )

    result_context = dispatcher.dispatch(
        ["invalid_agent"],
        context,
    )

    assert result_context is context
    assert not context.has_result("invalid_agent")
    assert len(context.errors) == 1

    error = context.errors[0]

    assert error.agent_name == "invalid_agent"
    assert error.exception_type == "AttributeError"

    assert error.message == (
        "Agent 'invalid_agent' does not implement execute()."
    )


def test_dispatch_raises_when_fail_fast_is_enabled() -> None:
    registry = AgentRegistry()

    register_agent(
        registry,
        name="invalid_agent",
        agent=InvalidAgent(),
    )

    dispatcher = Dispatcher(registry)

    context = ExecutionContext(
        request="Run invalid agent.",
    )

    with pytest.raises(
        AttributeError,
        match="does not implement execute",
    ):
        dispatcher.dispatch(
            ["invalid_agent"],
            context,
            fail_fast=True,
        )

    assert len(context.errors) == 1

    error = context.errors[0]

    assert error.agent_name == "invalid_agent"
    assert error.exception_type == "AttributeError"

    assert error.message == (
        "Agent 'invalid_agent' does not implement execute()."
    )


def test_execution_context_defaults_are_independent() -> None:
    first_context = ExecutionContext(
        request="First request.",
    )

    second_context = ExecutionContext(
        request="Second request.",
    )

    first_context.set_result(
        "controller",
        "first-result",
    )

    first_context.metadata["company_id"] = "company-001"

    assert first_context.results == {
        "controller": "first-result",
    }

    assert second_context.results == {}
    assert second_context.metadata == {}
    assert second_context.errors == []