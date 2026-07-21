"""Tests for the high-level orchestrator service."""

from __future__ import annotations

import pytest

from src.orchestrator.context import ExecutionContext
from src.orchestrator.orchestrator import Orchestrator


class FakePlanner:
    """Planner test double."""

    def __init__(self, plan: list[str]) -> None:
        self.plan_result = plan
        self.received_request: str | None = None
        self.call_count = 0

    def plan(self, request: str) -> list[str]:
        self.received_request = request
        self.call_count += 1
        return self.plan_result


class FakeDispatcher:
    """Dispatcher test double."""

    def __init__(self) -> None:
        self.received_plan: list[str] | None = None
        self.received_context: ExecutionContext | None = None
        self.call_count = 0

    def dispatch(
        self,
        *,
        plan: list[str],
        context: ExecutionContext,
    ) -> ExecutionContext:
        self.received_plan = plan
        self.received_context = context
        self.call_count += 1

        context.results["test_agent"] = {
            "status": "completed",
        }

        return context


def test_run_coordinates_planner_and_dispatcher() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    result = orchestrator.run("Run the financial review.")

    assert planner.call_count == 1
    assert planner.received_request == "Run the financial review."

    assert dispatcher.call_count == 1
    assert dispatcher.received_plan == ["test_agent"]
    assert dispatcher.received_context is result

    assert result.request == "Run the financial review."
    assert result.results["test_agent"] == {
        "status": "completed",
    }


def test_run_strips_request_whitespace() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    result = orchestrator.run(
        "   Review the trial balance.   ",
    )

    assert result.request == "Review the trial balance."
    assert planner.received_request == "Review the trial balance."


def test_run_rejects_empty_request() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    with pytest.raises(
        ValueError,
        match="Request cannot be empty",
    ):
        orchestrator.run("   ")

    assert planner.call_count == 0
    assert dispatcher.call_count == 0


def test_run_rejects_non_string_request() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    with pytest.raises(
        TypeError,
        match="Request must be a string",
    ):
        orchestrator.run(123)  # type: ignore[arg-type]

    assert planner.call_count == 0
    assert dispatcher.call_count == 0


def test_run_copies_metadata() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    metadata = {
        "company_id": "company-001",
    }

    result = orchestrator.run(
        "Run the financial review.",
        metadata=metadata,
    )

    assert result.metadata == metadata
    assert result.metadata is not metadata


def test_run_copies_initial_results() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    initial_results = {
        "general_ledger": {
            "entries_processed": 20,
        }
    }

    result = orchestrator.run(
        "Review the ledger.",
        initial_results=initial_results,
    )

    assert result.results["general_ledger"] == {
        "entries_processed": 20,
    }
    assert result.results is not initial_results


def test_run_uses_independent_default_dictionaries() -> None:
    planner = FakePlanner(["test_agent"])
    dispatcher = FakeDispatcher()

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    first_result = orchestrator.run("First request.")
    second_result = orchestrator.run("Second request.")

    first_result.metadata["company_id"] = "company-001"
    first_result.results["extra"] = "value"

    assert second_result.metadata == {}
    assert "extra" not in second_result.results