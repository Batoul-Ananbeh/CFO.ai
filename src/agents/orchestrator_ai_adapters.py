"""Adapters connecting CFO.ai AI agents to the Orchestrator."""

from __future__ import annotations

from typing import Any

from src.agents.chief_cfo_ai_agent import ChiefCFOAIAgent
from src.agents.controller_ai_agent import ControllerAIAgent
from src.agents.forecast_ai_agent import ForecastAIAgent
from src.agents.general_ledger_ai_agent import (
    GeneralLedgerAIAgent,
)
from src.agents.risk_ai_agent import RiskAIAgent
from src.agents.strategy_ai_agent import StrategyAIAgent
from src.ai.context_utils import (
    attach_ai_metadata,
    build_verified_agent_context,
)


class GeneralLedgerAIOrchestratorAdapter:
    agent_name = "general_ledger_ai"

    def __init__(self, ai_agent: GeneralLedgerAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            ("general_ledger",),
        )

        result = self.ai_agent.explain_verified_result(
            result_context=verified_context,
            user_input=(
                "Explain the verified General Ledger result "
                "and recommend review actions."
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ControllerAIOrchestratorAdapter:
    agent_name = "controller_ai"

    def __init__(self, ai_agent: ControllerAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "general_ledger",
                "general_ledger_ai",
                "controller",
            ),
        )

        result = self.ai_agent.review(
            verified_context=verified_context,
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class RiskAIOrchestratorAdapter:
    agent_name = "risk_ai"

    def __init__(self, ai_agent: RiskAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "general_ledger",
                "controller",
                "controller_ai",
            ),
        )

        result = self.ai_agent.assess(
            verified_context=verified_context,
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ForecastAIOrchestratorAdapter:
    agent_name = "forecast_ai"

    def __init__(self, ai_agent: ForecastAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "general_ledger",
                "controller",
                "risk_ai",
            ),
        )

        result = self.ai_agent.analyze(
            verified_context=verified_context,
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class StrategyAIOrchestratorAdapter:
    agent_name = "strategy_ai"

    def __init__(self, ai_agent: StrategyAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "risk_ai",
                "forecast_ai",
            ),
        )

        result = self.ai_agent.recommend(
            verified_context=verified_context,
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ChiefCFOAIOrchestratorAdapter:
    agent_name = "chief_cfo_ai"

    def __init__(self, ai_agent: ChiefCFOAIAgent) -> None:
        self.ai_agent = ai_agent

    def execute(self, context: Any) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "general_ledger",
                "general_ledger_ai",
                "controller",
                "controller_ai",
                "risk_ai",
                "forecast_ai",
                "strategy_ai",
            ),
        )

        result = self.ai_agent.summarize(
            verified_context=verified_context,
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )
