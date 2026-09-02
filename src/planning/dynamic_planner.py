"""Dynamic execution planning for CFO.ai."""

from __future__ import annotations

from dataclasses import dataclass

from src.planning.dependency_resolver import (
    AgentDependencyResolver,
)
from src.planning.intent_analyzer import (
    FinancialIntentAnalyzer,
)
from src.planning.intents import FinancialIntent


@dataclass(frozen=True, slots=True)
class DynamicPlanResult:
    """Auditable result produced by the dynamic planner."""

    request: str
    detected_intents: tuple[FinancialIntent, ...]
    execution_plan: tuple[str, ...]


class DynamicCFOPlanner:
    """
    Build the minimum valid agent plan for a financial request.

    The plan remains compatible with the existing Orchestrator
    because plan() returns list[str].
    """

    def __init__(
        self,
        intent_analyzer: FinancialIntentAnalyzer | None = None,
        dependency_resolver: AgentDependencyResolver | None = None,
    ) -> None:
        self.intent_analyzer = (
            intent_analyzer
            or FinancialIntentAnalyzer()
        )

        self.dependency_resolver = (
            dependency_resolver
            or AgentDependencyResolver()
        )

        self.last_plan_result: DynamicPlanResult | None = None

    def plan(
        self,
        request: str,
    ) -> list[str]:
        """Return an ordered Orchestrator execution plan."""

        intents = self.intent_analyzer.analyze(request)

        execution_plan = (
            self.dependency_resolver.resolve_intents(
                intents
            )
        )

        ordered_intents = tuple(
            sorted(
                intents,
                key=lambda intent: intent.value,
            )
        )

        self.last_plan_result = DynamicPlanResult(
            request=request,
            detected_intents=ordered_intents,
            execution_plan=tuple(execution_plan),
        )

        return execution_plan
