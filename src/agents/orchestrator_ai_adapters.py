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


def _resolve_user_input(
    context: Any,
    *,
    fallback: str,
) -> str:
    """Return the original user request when available."""

    request = getattr(
        context,
        "request",
        None,
    )

    if isinstance(request, str):
        normalized_request = request.strip()

        if normalized_request:
            return normalized_request

    return fallback


class GeneralLedgerAIOrchestratorAdapter:
    """Connect GeneralLedgerAIAgent to ExecutionContext."""

    agent_name = "general_ledger_ai"

    def __init__(
        self,
        ai_agent: GeneralLedgerAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "general_ledger",
            ),
        )

        result = self.ai_agent.explain_verified_result(
            result_context=verified_context,
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Explain the verified General Ledger result "
                    "and recommend review actions."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ControllerAIOrchestratorAdapter:
    """Connect ControllerAIAgent to ExecutionContext."""

    agent_name = "controller_ai"

    def __init__(
        self,
        ai_agent: ControllerAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
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
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Explain the Controller review, identify "
                    "control findings and required corrections."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class RiskAIOrchestratorAdapter:
    """Connect RiskAIAgent to ExecutionContext."""

    agent_name = "risk_ai"

    def __init__(
        self,
        ai_agent: RiskAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
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
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Assess the verified financial and control "
                    "risks and recommend controls."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ForecastAIOrchestratorAdapter:
    """Connect ForecastAIAgent to ExecutionContext."""

    agent_name = "forecast_ai"

    def __init__(
        self,
        ai_agent: ForecastAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
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
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Explain the verified financial forecast, "
                    "assumptions, risks and recommendations."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class StrategyAIOrchestratorAdapter:
    """Connect StrategyAIAgent to ExecutionContext."""

    agent_name = "strategy_ai"

    def __init__(
        self,
        ai_agent: StrategyAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
        verified_context = build_verified_agent_context(
            context,
            (
                "risk_ai",
                "forecast_ai",
            ),
        )

        result = self.ai_agent.recommend(
            verified_context=verified_context,
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Create financial strategy recommendations "
                    "from the verified context."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )


class ChiefCFOAIOrchestratorAdapter:
    """Connect ChiefCFOAIAgent to ExecutionContext."""

    agent_name = "chief_cfo_ai"

    def __init__(
        self,
        ai_agent: ChiefCFOAIAgent,
    ) -> None:
        self.ai_agent = ai_agent

    def execute(
        self,
        context: Any,
    ) -> dict[str, Any]:
        required_results = (
            "general_ledger",
            "general_ledger_ai",
            "controller",
            "controller_ai",
            "risk_ai",
        )

        optional_results = tuple(
            result_name
            for result_name in (
                "forecast_ai",
                "strategy_ai",
                "data_sufficiency",
            )
            if self._has_result(
                context,
                result_name,
            )
        )

        verified_context = build_verified_agent_context(
            context,
            required_results + optional_results,
        )

        result = self.ai_agent.summarize(
            verified_context=verified_context,
            user_input=_resolve_user_input(
                context,
                fallback=(
                    "Create an executive CFO brief from all "
                    "verified specialized-agent results."
                ),
            ),
        )

        return attach_ai_metadata(
            result,
            self.ai_agent.provider,
        )

    @staticmethod
    def _has_result(
        context: Any,
        result_name: str,
    ) -> bool:
        """Return whether an optional result is available."""

        if hasattr(context, "has_result"):
            return bool(
                context.has_result(result_name)
            )

        results = getattr(
            context,
            "results",
            None,
        )

        return (
            isinstance(results, dict)
            and result_name in results
        )
