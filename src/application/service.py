"""High-level application service for CFO.ai."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.application.models import (
    CFOAnalysisRequest,
    CFOAnalysisResponse,
)
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.runtime.hybrid_runtime import (
    UnifiedCFORuntime,
)


class CFOApplicationService:
    """
    Provide one stable entry point for CFO.ai consumers.

    API endpoints, dashboards, pharmacy systems, and voice agents
    should call this service instead of directly coordinating
    workflows, planners, or agents.
    """

    def __init__(
        self,
        *,
        runtime: UnifiedCFORuntime,
        persistence: (
            AnalysisPersistenceService | None
        ) = None,
    ) -> None:
        self._runtime = runtime
        self._persistence = persistence

    def analyze(
        self,
        analysis_request: (
            CFOAnalysisRequest
            | Mapping[str, Any]
        ),
    ) -> CFOAnalysisResponse:
        """Execute and optionally persist a complete CFO analysis."""

        normalized_request = self._normalize_request(
            analysis_request
        )

        execution_metadata = dict(
            normalized_request.metadata
        )

        correlation_id = self._resolve_correlation_id(
            execution_metadata
        )

        execution_metadata[
            "correlation_id"
        ] = correlation_id

        if self._persistence is not None:
            self._persistence.ensure_correlation_id_available(
                correlation_id
            )

        started_at = datetime.now(
            timezone.utc
        )

        runtime_result = self._runtime.run(
            normalized_request.request,
            financial_input=(
                normalized_request.financial_input
            ),
            metadata=execution_metadata,
        )

        completed_at = datetime.now(
            timezone.utc
        )

        response = (
            CFOAnalysisResponse.from_runtime_result(
                runtime_result
            )
        )

        if response.correlation_id is None:
            response.correlation_id = correlation_id

        persistence_request = (
            normalized_request.model_copy(
                update={
                    "metadata": execution_metadata,
                }
            )
        )

        if self._persistence is not None:
            response.analysis_id = (
                self._persistence.persist(
                    analysis_request=(
                        persistence_request
                    ),
                    response=response,
                    started_at=started_at,
                    completed_at=completed_at,
                )
            )

        return response

    def analyze_to_dict(
        self,
        analysis_request: (
            CFOAnalysisRequest
            | Mapping[str, Any]
        ),
    ) -> dict[str, Any]:
        """Execute an analysis and return a JSON-ready dictionary."""

        response = self.analyze(
            analysis_request
        )

        return response.model_dump(
            mode="json"
        )

    @staticmethod
    def _resolve_correlation_id(
        metadata: Mapping[str, Any],
    ) -> str:
        """Use an existing correlation ID or create one."""

        raw_value = metadata.get(
            "correlation_id"
        )

        if raw_value is None:
            return (
                f"CORR-{uuid4().hex[:16].upper()}"
            )

        if not isinstance(
            raw_value,
            str,
        ):
            raise TypeError(
                "correlation_id must be a string."
            )

        normalized_value = raw_value.strip()

        if not normalized_value:
            raise ValueError(
                "correlation_id must not be empty."
            )

        return normalized_value

    @staticmethod
    def _normalize_request(
        analysis_request: (
            CFOAnalysisRequest
            | Mapping[str, Any]
        ),
    ) -> CFOAnalysisRequest:
        """Validate a model or raw mapping request."""

        if isinstance(
            analysis_request,
            CFOAnalysisRequest,
        ):
            return analysis_request

        if not isinstance(
            analysis_request,
            Mapping,
        ):
            raise TypeError(
                "Analysis request must be "
                "CFOAnalysisRequest or a mapping."
            )

        return CFOAnalysisRequest.model_validate(
            dict(analysis_request)
        )
