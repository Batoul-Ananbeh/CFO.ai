"""Contracts used by the unified CFO runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class DeterministicFinanceRunner(Protocol):
    """
    Contract for the verified accounting and finance layer.

    A concrete implementation may call the General Ledger workflow,
    Controller workflow, database services, or another deterministic
    financial engine.
    """

    def run(
        self,
        *,
        financial_input: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any] | Any:
        """Return verified financial results."""
        ...
