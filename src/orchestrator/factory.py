"""Factories for constructing CFO.ai orchestrators."""

from __future__ import annotations

from collections.abc import Sequence

from src.orchestrator.contracts import ExecutionPlanner
from src.orchestrator.dispatcher import Dispatcher
from src.orchestrator.orchestrator import Orchestrator
from src.orchestrator.registry import AgentRegistry
from src.planning.dependency_resolver import (
    CANONICAL_AGENT_ORDER,
)
from src.planning.dynamic_planner import (
    DynamicCFOPlanner,
)


def find_missing_dynamic_agents(
    registry: AgentRegistry,
    required_agents: Sequence[str] = CANONICAL_AGENT_ORDER,
) -> tuple[str, ...]:
    """Return dynamic agents that are not registered."""

    return tuple(
        agent_name
        for agent_name in required_agents
        if not registry.contains(agent_name)
    )


def validate_dynamic_agent_registry(
    registry: AgentRegistry,
) -> None:
    """Ensure all dynamic CFO agents are registered."""

    missing_agents = find_missing_dynamic_agents(
        registry
    )

    if not missing_agents:
        return

    missing_text = ", ".join(missing_agents)

    raise ValueError(
        "Dynamic CFO registry is missing required agents: "
        f"{missing_text}."
    )


def build_dynamic_orchestrator(
    *,
    registry: AgentRegistry,
    planner: ExecutionPlanner | None = None,
    validate_registry: bool = True,
) -> Orchestrator:
    """
    Build an Orchestrator powered by DynamicCFOPlanner.

    The registry may contain real agents, adapters, or test
    doubles, as long as each registered object implements
    execute(context=...).
    """

    if validate_registry:
        validate_dynamic_agent_registry(
            registry
        )

    selected_planner = (
        planner
        if planner is not None
        else DynamicCFOPlanner()
    )

    dispatcher = Dispatcher(
        registry=registry
    )

    return Orchestrator(
        planner=selected_planner,
        dispatcher=dispatcher,
    )
