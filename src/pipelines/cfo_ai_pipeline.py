"""CFO.ai specialized-agent orchestration pipeline."""

from __future__ import annotations

from typing import Any

from src.agents.chief_cfo_ai_agent import ChiefCFOAIAgent
from src.agents.controller_ai_agent import ControllerAIAgent
from src.agents.forecast_ai_agent import ForecastAIAgent
from src.agents.general_ledger_ai_agent import (
    GeneralLedgerAIAgent,
)
from src.agents.orchestrator_ai_adapters import (
    ChiefCFOAIOrchestratorAdapter,
    ControllerAIOrchestratorAdapter,
    ForecastAIOrchestratorAdapter,
    GeneralLedgerAIOrchestratorAdapter,
    RiskAIOrchestratorAdapter,
    StrategyAIOrchestratorAdapter,
)
from src.agents.risk_ai_agent import RiskAIAgent
from src.agents.strategy_ai_agent import StrategyAIAgent
from src.ai.provider import LLMProvider


CFO_AI_EXECUTION_PLAN = [
    "general_ledger_ai",
    "controller_ai",
    "risk_ai",
    "forecast_ai",
    "strategy_ai",
    "chief_cfo_ai",
]


class CFOAIPlanner:
    """
    Planner for the complete CFO.ai specialized-agent pipeline.

    Deterministic General Ledger and Controller results are expected
    to already exist in the initial ExecutionContext.
    """

    def plan(
        self,
        request: str,
    ) -> list[str]:
        del request

        return CFO_AI_EXECUTION_PLAN.copy()


def configure_cfo_ai_registry(
    registry: Any,
    provider: LLMProvider,
) -> Any:
    """
    Register the complete CFO.ai AI pipeline.

    The registry object must support:

        registry.register(
            name=...,
            agent=...,
            required_inputs=...,
        )
    """

    general_ledger_ai = GeneralLedgerAIAgent(
        provider=provider,
    )

    controller_ai = ControllerAIAgent(
        provider=provider,
    )

    risk_ai = RiskAIAgent(
        provider=provider,
    )

    forecast_ai = ForecastAIAgent(
        provider=provider,
    )

    strategy_ai = StrategyAIAgent(
        provider=provider,
    )

    chief_cfo_ai = ChiefCFOAIAgent(
        provider=provider,
    )

    registry.register(
        name="general_ledger_ai",
        agent=GeneralLedgerAIOrchestratorAdapter(
            ai_agent=general_ledger_ai,
        ),
        required_inputs={
            "general_ledger",
        },
    )

    registry.register(
        name="controller_ai",
        agent=ControllerAIOrchestratorAdapter(
            ai_agent=controller_ai,
        ),
        required_inputs={
            "general_ledger",
            "general_ledger_ai",
            "controller",
        },
    )

    registry.register(
        name="risk_ai",
        agent=RiskAIOrchestratorAdapter(
            ai_agent=risk_ai,
        ),
        required_inputs={
            "controller",
            "controller_ai",
        },
    )

    registry.register(
        name="forecast_ai",
        agent=ForecastAIOrchestratorAdapter(
            ai_agent=forecast_ai,
        ),
        required_inputs={
            "risk_ai",
        },
    )

    registry.register(
        name="strategy_ai",
        agent=StrategyAIOrchestratorAdapter(
            ai_agent=strategy_ai,
        ),
        required_inputs={
            "risk_ai",
            "forecast_ai",
        },
    )

    registry.register(
        name="chief_cfo_ai",
        agent=ChiefCFOAIOrchestratorAdapter(
            ai_agent=chief_cfo_ai,
        ),
        required_inputs={
            "general_ledger_ai",
            "controller_ai",
            "risk_ai",
            "forecast_ai",
            "strategy_ai",
        },
    )

    return registry
