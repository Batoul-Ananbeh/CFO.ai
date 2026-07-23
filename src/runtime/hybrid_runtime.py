"""Unified deterministic and AI runtime for CFO.ai."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ai.provider import LLMProvider
from src.orchestrator.errors import ExecutionError
from src.pipelines.cfo_ai_pipeline import (
    build_cfo_ai_orchestrator,
)
from src.planning.dynamic_planner import DynamicCFOPlanner
from src.runtime.contracts import DeterministicFinanceRunner
from src.runtime.financial_accuracy import (
    apply_execution_policy,
    assess_financial_accuracy,
)
from src.runtime.models import (
    HybridRuntimeResult,
    HybridRuntimeStatus,
)


class UnifiedCFORuntime:
    """
    Execute verified financial logic followed by selected AI agents.

    The deterministic runner produces trusted results such as:

    - general_ledger
    - controller

    The DynamicCFOPlanner then selects only the AI agents required
    for the user's request.
    """

    def __init__(
        self,
        *,
        deterministic_runner: DeterministicFinanceRunner,
        provider: LLMProvider,
        planner: DynamicCFOPlanner | None = None,
    ) -> None:
        self._deterministic_runner = deterministic_runner
        self._planner = planner or DynamicCFOPlanner()

        self._orchestrator = build_cfo_ai_orchestrator(
            provider=provider,
            planner=self._planner,
        )

    def run(
        self,
        request: str,
        *,
        financial_input: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> HybridRuntimeResult:
        """Run the complete verified and intelligent CFO process."""

        normalized_request = self._normalize_request(
            request
        )

        normalized_financial_input = self._copy_mapping(
            financial_input,
            field_name="Financial input",
        )

        normalized_metadata = self._copy_mapping(
            metadata or {},
            field_name="Metadata",
        )

        requested_plan = tuple(
            self._planner.plan(
                normalized_request
            )
        )

        try:
            raw_verified_results = (
                self._deterministic_runner.run(
                    financial_input=normalized_financial_input,
                    metadata=normalized_metadata,
                )
            )

            verified_results = (
                self._coerce_verified_results(
                    raw_verified_results
                )
            )

        except Exception as exception:
            error = ExecutionError.from_exception(
                agent_name="deterministic_finance",
                exception=exception,
            )

            return HybridRuntimeResult(
                request=normalized_request,
                execution_plan=requested_plan,
                executed_agents=(),
                verified_results={},
                ai_results={},
                errors=(error,),
                status=HybridRuntimeStatus.FAILED,
            )

        accuracy_assessment = assess_financial_accuracy(
            metadata=normalized_metadata,
            verified_results=verified_results,
        )

        verified_results["data_sufficiency"] = (
            accuracy_assessment.as_context()
        )

        execution_plan = tuple(
            apply_execution_policy(
                requested_plan,
                assessment=accuracy_assessment,
            )
        )

        enriched_metadata = {
            **normalized_metadata,
            "financial_accuracy_policy": (
                accuracy_assessment.as_context()
            ),
        }

        context = self._orchestrator.run(
            normalized_request,
            metadata=enriched_metadata,
            initial_results=verified_results,
            execution_plan=list(execution_plan),
        )

        executed_agents = tuple(
            agent_name
            for agent_name in execution_plan
            if context.has_result(agent_name)
        )

        ai_results = {
            agent_name: context.get_result(agent_name)
            for agent_name in executed_agents
        }

        status = self._resolve_status(
            executed_agents=executed_agents,
            errors=context.errors,
        )

        return HybridRuntimeResult(
            request=normalized_request,
            execution_plan=execution_plan,
            executed_agents=executed_agents,
            verified_results=dict(verified_results),
            ai_results=ai_results,
            errors=tuple(context.errors),
            status=status,
        )

    @staticmethod
    def _resolve_status(
        *,
        executed_agents: tuple[str, ...],
        errors: list[ExecutionError],
    ) -> HybridRuntimeStatus:
        """Resolve the final status from execution results."""

        if not errors:
            return HybridRuntimeStatus.COMPLETED

        if executed_agents:
            return HybridRuntimeStatus.PARTIAL

        return HybridRuntimeStatus.FAILED

    @staticmethod
    def _normalize_request(
        request: str,
    ) -> str:
        """Validate and normalize the user's request."""

        if not isinstance(request, str):
            raise TypeError(
                "Request must be a string."
            )

        normalized_request = request.strip()

        if not normalized_request:
            raise ValueError(
                "Request cannot be empty."
            )

        return normalized_request

    @staticmethod
    def _copy_mapping(
        value: Mapping[str, Any],
        *,
        field_name: str,
    ) -> dict[str, Any]:
        """Validate and copy a mapping input."""

        if not isinstance(value, Mapping):
            raise TypeError(
                f"{field_name} must be a mapping."
            )

        return dict(value)

    @staticmethod
    def _coerce_verified_results(
        value: Any,
    ) -> dict[str, Any]:
        """
        Normalize deterministic results.

        Supports either a mapping or an object such as
        ExecutionContext that exposes a results mapping.
        """

        if isinstance(value, Mapping):
            return dict(value)

        results = getattr(
            value,
            "results",
            None,
        )

        if isinstance(results, Mapping):
            return dict(results)

        raise TypeError(
            "Deterministic runner must return a mapping "
            "or an object containing a results mapping."
        )


def build_unified_cfo_runtime(
    *,
    deterministic_runner: DeterministicFinanceRunner,
    provider: LLMProvider,
    planner: DynamicCFOPlanner | None = None,
) -> UnifiedCFORuntime:
    """Build the unified CFO.ai runtime."""

    return UnifiedCFORuntime(
        deterministic_runner=deterministic_runner,
        provider=provider,
        planner=planner,
    )
