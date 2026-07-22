"""CFO.ai specialized-agent orchestration pipeline."""

from __future__ import annotations

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
from src.orchestrator.contracts import ExecutionPlanner
from src.orchestrator.factory import build_dynamic_orchestrator
from src.orchestrator.orchestrator import Orchestrator
from src.orchestrator.registry import AgentRegistry


CFO_AI_EXECUTION_PLAN = [
    "general_ledger_ai",
    "controller_ai",
    "risk_ai",
    "forecast_ai",
    "strategy_ai",
    "chief_cfo_ai",
]


class CFOAIPlanner:
    """Planner for the complete fixed CFO AI pipeline."""

    def plan(
        self,
        request: str,
    ) -> list[str]:
        del request

        return CFO_AI_EXECUTION_PLAN.copy()


def configure_cfo_ai_registry(
    registry: AgentRegistry,
    provider: LLMProvider,
) -> AgentRegistry:
    """Register the real CFO.ai AI agents and adapters."""

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
        capabilities={
            "general_ledger_explanation",
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
        capabilities={
            "controller_review",
        },
    )

    registry.register(
        name="risk_ai",
        agent=RiskAIOrchestratorAdapter(
            ai_agent=risk_ai,
        ),
        required_inputs={
            "general_ledger",
            "controller",
            "controller_ai",
        },
        capabilities={
            "risk_analysis",
            "internal_audit",
        },
    )

    registry.register(
        name="forecast_ai",
        agent=ForecastAIOrchestratorAdapter(
            ai_agent=forecast_ai,
        ),
        required_inputs={
            "general_ledger",
            "controller",
            "risk_ai",
        },
        capabilities={
            "forecast_analysis",
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
        capabilities={
            "financial_strategy",
        },
    )

    registry.register(
        name="chief_cfo_ai",
        agent=ChiefCFOAIOrchestratorAdapter(
            ai_agent=chief_cfo_ai,
        ),
        required_inputs={
            "general_ledger",
            "general_ledger_ai",
            "controller",
            "controller_ai",
            "risk_ai",
            "forecast_ai",
            "strategy_ai",
        },
        capabilities={
            "executive_cfo_brief",
        },
    )

    return registry


def build_cfo_ai_orchestrator(
    *,
    provider: LLMProvider,
    planner: ExecutionPlanner | None = None,
    registry: AgentRegistry | None = None,
) -> Orchestrator:
    """
    Build the real CFO.ai dynamic multi-agent orchestrator.

    The supplied provider may be Gemini in production or a fake
    provider during offline tests.
    """

    selected_registry = (
        registry
        if registry is not None
        else AgentRegistry()
    )

    configure_cfo_ai_registry(
        registry=selected_registry,
        provider=provider,
    )

    return build_dynamic_orchestrator(
        registry=selected_registry,
        planner=planner,
        validate_registry=True,
    )
