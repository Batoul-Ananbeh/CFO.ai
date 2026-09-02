"""Intent models used by the CFO.ai dynamic planner."""

from __future__ import annotations

from enum import StrEnum


class FinancialIntent(StrEnum):
    """Supported high-level financial request intents."""

    GENERAL_LEDGER = "general_ledger"
    CONTROLLER_REVIEW = "controller_review"
    RISK_ANALYSIS = "risk_analysis"
    FORECAST_ANALYSIS = "forecast_analysis"
    STRATEGY_ANALYSIS = "strategy_analysis"
    EXECUTIVE_CFO_BRIEF = "executive_cfo_brief"
