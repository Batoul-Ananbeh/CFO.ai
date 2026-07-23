"""Real deterministic finance runner for CFO.ai."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from src.ai.provider import LLMProvider
from src.planning.dynamic_planner import DynamicCFOPlanner
from src.runtime.hybrid_runtime import UnifiedCFORuntime
from src.schemas.general_ledger import LedgerTransactionInput
from src.workflows.gl_controller_workflow import (
    GLControllerWorkflow,
)


class GLControllerDeterministicRunner:
    """
    Execute the real General Ledger to Controller workflow.

    The runner validates raw transaction data, executes the
    LangGraph workflow, and returns verified financial results.
    """

    def __init__(
        self,
        workflow: GLControllerWorkflow | None = None,
    ) -> None:
        self._workflow = (
            workflow
            if workflow is not None
            else GLControllerWorkflow()
        )

    def run(
        self,
        *,
        financial_input: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the verified GL-to-Controller workflow."""

        if not isinstance(
            financial_input,
            Mapping,
        ):
            raise TypeError(
                "Financial input must be a mapping."
            )

        normalized_metadata = self._normalize_metadata(
            metadata
        )

        input_data = LedgerTransactionInput.model_validate(
            dict(financial_input)
        )

        correlation_id = self._resolve_correlation_id(
            normalized_metadata
        )

        workflow_result = self._workflow.run(
            input_data=input_data,
            correlation_id=correlation_id,
        )

        return {
            "general_ledger": (
                workflow_result.general_ledger_result
            ),
            "controller": (
                workflow_result.controller_result
            ),
            "gl_controller_workflow": {
                "correlation_id": (
                    workflow_result.correlation_id
                ),
                "final_status": (
                    workflow_result.final_status
                ),
                "summary": workflow_result.summary,
            },
        }

    @staticmethod
    def _normalize_metadata(
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Validate and copy optional execution metadata."""

        if metadata is None:
            return {}

        if not isinstance(metadata, Mapping):
            raise TypeError(
                "Metadata must be a mapping."
            )

        return dict(metadata)

    @staticmethod
    def _resolve_correlation_id(
        metadata: Mapping[str, Any],
    ) -> str:
        """Use the supplied correlation ID or generate one."""

        supplied_value = metadata.get(
            "correlation_id"
        )

        if supplied_value is None:
            return (
                f"CORR-{uuid4().hex[:16].upper()}"
            )

        if not isinstance(supplied_value, str):
            raise TypeError(
                "correlation_id must be a string."
            )

        normalized_value = supplied_value.strip()

        if not normalized_value:
            raise ValueError(
                "correlation_id must not be empty."
            )

        return normalized_value


def build_gl_controller_cfo_runtime(
    *,
    provider: LLMProvider,
    workflow: GLControllerWorkflow | None = None,
    planner: DynamicCFOPlanner | None = None,
) -> UnifiedCFORuntime:
    """
    Build the real deterministic and AI CFO runtime.

    The provider may be Gemini during real execution or a fake
    provider during automated tests.
    """

    deterministic_runner = (
        GLControllerDeterministicRunner(
            workflow=workflow,
        )
    )

    return UnifiedCFORuntime(
        deterministic_runner=deterministic_runner,
        provider=provider,
        planner=planner,
    )
