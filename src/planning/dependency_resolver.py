"""Dependency resolution for CFO.ai specialized agents."""

from __future__ import annotations

from collections.abc import Iterable

from src.planning.intents import FinancialIntent


CANONICAL_AGENT_ORDER: tuple[str, ...] = (
    "general_ledger_ai",
    "controller_ai",
    "risk_ai",
    "forecast_ai",
    "strategy_ai",
    "chief_cfo_ai",
)


INTENT_TARGET_AGENT: dict[FinancialIntent, str] = {
    FinancialIntent.GENERAL_LEDGER: "general_ledger_ai",
    FinancialIntent.CONTROLLER_REVIEW: "controller_ai",
    FinancialIntent.RISK_ANALYSIS: "risk_ai",
    FinancialIntent.FORECAST_ANALYSIS: "forecast_ai",
    FinancialIntent.STRATEGY_ANALYSIS: "strategy_ai",
    FinancialIntent.EXECUTIVE_CFO_BRIEF: "chief_cfo_ai",
}


AGENT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "general_ledger_ai": (),
    "controller_ai": (
        "general_ledger_ai",
    ),
    "risk_ai": (
        "controller_ai",
    ),
    "forecast_ai": (
        "risk_ai",
    ),
    "strategy_ai": (
        "risk_ai",
        "forecast_ai",
    ),
    "chief_cfo_ai": (
        "general_ledger_ai",
        "controller_ai",
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
    ),
}


class AgentDependencyResolver:
    """Resolve all transitive dependencies for requested agents."""

    def resolve_intents(
        self,
        intents: Iterable[FinancialIntent],
    ) -> list[str]:
        """Convert financial intents into an ordered execution plan."""

        target_agents = {
            INTENT_TARGET_AGENT[intent]
            for intent in intents
        }

        return self.resolve_agents(target_agents)

    def resolve_agents(
        self,
        target_agents: Iterable[str],
    ) -> list[str]:
        """Resolve target agents and all required dependencies."""

        resolved_agents: set[str] = set()
        visiting_agents: set[str] = set()

        for agent_name in target_agents:
            self._visit(
                agent_name=agent_name,
                resolved_agents=resolved_agents,
                visiting_agents=visiting_agents,
            )

        return [
            agent_name
            for agent_name in CANONICAL_AGENT_ORDER
            if agent_name in resolved_agents
        ]

    def _visit(
        self,
        *,
        agent_name: str,
        resolved_agents: set[str],
        visiting_agents: set[str],
    ) -> None:
        """Perform depth-first dependency resolution."""

        if agent_name in resolved_agents:
            return

        if agent_name in visiting_agents:
            raise RuntimeError(
                f"Circular agent dependency detected at "
                f"{agent_name!r}."
            )

        if agent_name not in AGENT_DEPENDENCIES:
            raise KeyError(
                f"Unknown CFO.ai agent: {agent_name!r}."
            )

        visiting_agents.add(agent_name)

        for dependency_name in AGENT_DEPENDENCIES[
            agent_name
        ]:
            self._visit(
                agent_name=dependency_name,
                resolved_agents=resolved_agents,
                visiting_agents=visiting_agents,
            )

        visiting_agents.remove(agent_name)
        resolved_agents.add(agent_name)
