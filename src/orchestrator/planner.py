"""Planning logic for the CFO.ai orchestrator."""

from __future__ import annotations


class Planner:
    """Determine which agents should execute a user request."""

    def plan(self, request: str) -> list[str]:
        """
        Return the ordered list of agents required
        to satisfy the request.
        """
        text = request.strip().lower()

        if not text:
            raise ValueError("Request cannot be empty.")

        if any(
            keyword in text
            for keyword in (
                "journal",
                "ledger",
                "entry",
            )
        ):
            return ["general_ledger"]

        if any(
            keyword in text
            for keyword in (
                "trial balance",
                "controller",
                "review",
            )
        ):
            return ["controller"]

        raise ValueError(
            f"No execution plan found for request: '{request}'"
        )