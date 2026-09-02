"""Shared contracts for CFO.ai orchestration."""

from __future__ import annotations

from typing import Protocol


class ExecutionPlanner(Protocol):
    """Contract implemented by orchestration planners."""

    def plan(
        self,
        user_request: str,
    ) -> list[str]:
        """Return the ordered agents required for a request."""
        ...
