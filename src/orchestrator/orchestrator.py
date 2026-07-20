"""High-level orchestration service."""

from __future__ import annotations

from typing import Any

from src.orchestrator.context import ExecutionContext
from src.orchestrator.dispatcher import Dispatcher
from src.orchestrator.planner import Planner


class Orchestrator:
    """Coordinate planning and agent execution."""

    def __init__(
        self,
        *,
        planner: Planner,
        dispatcher: Dispatcher,
    ) -> None:
        self._planner = planner
        self._dispatcher = dispatcher

    def run(
        self,
        request: str,
        *,
        metadata: dict[str, Any] | None = None,
        initial_results: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        """Plan and execute a single orchestration request."""

        normalized_request = self._normalize_request(request)

        context = ExecutionContext(
            request=normalized_request,
            metadata=dict(metadata or {}),
            results=dict(initial_results or {}),
        )

        plan = self._planner.plan(normalized_request)

        return self._dispatcher.dispatch(
            plan=plan,
            context=context,
        )

    @staticmethod
    def _normalize_request(request: str) -> str:
        """Validate and normalize a user request."""

        if not isinstance(request, str):
            raise TypeError("Request must be a string.")

        normalized_request = request.strip()

        if not normalized_request:
            raise ValueError("Request cannot be empty.")

        return normalized_request