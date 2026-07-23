"""Persistent company CFO reports built from verified monthly aggregation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.agents.chief_cfo_ai_agent import (
    ChiefCFOAIAgent,
)
from src.agents.forecast_ai_agent import (
    ForecastAIAgent,
)
from src.agents.risk_ai_agent import (
    RiskAIAgent,
)
from src.agents.strategy_ai_agent import (
    StrategyAIAgent,
)
from src.ai.context_utils import (
    attach_ai_metadata,
)
from src.ai.provider import LLMProvider
from src.application.models import (
    CFOAnalysisRequest,
    CFOAnalysisResponse,
    CFOExecutionError,
)
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.ingestion.aggregation import (
    MonthlyAggregationService,
)
from src.orchestrator.errors import (
    ExecutionError,
)
from src.runtime.models import (
    HybridRuntimeStatus,
)


_COMPANY_REPORT_PLAN = [
    "risk_ai",
    "forecast_ai",
    "strategy_ai",
    "chief_cfo_ai",
]

_REQUIRED_CAPABILITIES = {
    "multi_period_financial_history",
    "company_level_financial_context",
}


class CompanyCFOReportRequest(BaseModel):
    """Request controls for one batch-level company report."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    correlation_id: str = Field(
        min_length=1,
        max_length=100,
    )
    request: str = Field(
        default=(
            "Prepare a company CFO report from the verified monthly "
            "financial summaries. Keep currencies separate and identify "
            "all evidence limitations."
        ),
        min_length=1,
    )


class CompanyCFOReportService:
    """Orchestrate and persist a company report from one ingestion batch."""

    def __init__(
        self,
        *,
        aggregation: MonthlyAggregationService,
        provider: LLMProvider,
        persistence: AnalysisPersistenceService | None = None,
    ) -> None:
        self._aggregation = aggregation
        self._provider = provider
        self._persistence = persistence

    def generate(
        self,
        *,
        batch_id: str,
        report_request: CompanyCFOReportRequest,
    ) -> CFOAnalysisResponse:
        """Generate a deterministic-limited or full intelligent report."""

        if self._persistence is not None:
            self._persistence.ensure_correlation_id_available(
                report_request.correlation_id
            )

        started_at = datetime.now(
            timezone.utc
        )
        aggregation = self._aggregation.aggregate(
            batch_id
        )
        aggregation_payload = aggregation.model_dump(
            mode="json"
        )
        data_profile = aggregation_payload[
            "data_profile"
        ]
        verified_results = {
            "monthly_aggregation": aggregation_payload,
            "data_profile": data_profile,
        }
        capabilities = set(
            data_profile[
                "verified_capabilities"
            ]
        )

        if not _REQUIRED_CAPABILITIES.issubset(
            capabilities
        ):
            response = self._insufficient_data_response(
                report_request=report_request,
                verified_results=verified_results,
            )
        else:
            response = self._execute_agents(
                report_request=report_request,
                verified_results=verified_results,
            )

        completed_at = datetime.now(
            timezone.utc
        )

        if self._persistence is not None:
            persistence_request = CFOAnalysisRequest(
                request=report_request.request,
                financial_input={
                    "batch_id": batch_id,
                    "analysis_scope": (
                        "company_monthly_aggregation"
                    ),
                },
                metadata={
                    "correlation_id": (
                        report_request.correlation_id
                    ),
                    "company_id": aggregation.company_id,
                    "company_code": aggregation.company_code,
                    "batch_id": batch_id,
                    "analysis_scope": (
                        "company_monthly_aggregation"
                    ),
                },
            )
            response.analysis_id = (
                self._persistence.persist(
                    analysis_request=persistence_request,
                    response=response,
                    started_at=started_at,
                    completed_at=completed_at,
                )
            )

        return response

    def _execute_agents(
        self,
        *,
        report_request: CompanyCFOReportRequest,
        verified_results: dict[str, Any],
    ) -> CFOAnalysisResponse:
        ai_results: dict[str, Any] = {}
        executed_agents: list[str] = []
        errors: list[CFOExecutionError] = []
        base_context = {
            "monthly_aggregation": verified_results[
                "monthly_aggregation"
            ],
            "data_profile": verified_results[
                "data_profile"
            ],
        }
        agents = [
            (
                "risk_ai",
                RiskAIAgent(
                    provider=self._provider
                ),
                "assess",
            ),
            (
                "forecast_ai",
                ForecastAIAgent(
                    provider=self._provider
                ),
                "analyze",
            ),
            (
                "strategy_ai",
                StrategyAIAgent(
                    provider=self._provider
                ),
                "recommend",
            ),
            (
                "chief_cfo_ai",
                ChiefCFOAIAgent(
                    provider=self._provider
                ),
                "summarize",
            ),
        ]

        for agent_name, agent, method_name in agents:
            context = {
                **base_context,
                "specialized_agent_results": dict(
                    ai_results
                ),
            }

            try:
                method = getattr(
                    agent,
                    method_name,
                )
                result = method(
                    verified_context=context,
                    user_input=report_request.request,
                )
                ai_results[agent_name] = (
                    attach_ai_metadata(
                        result,
                        self._provider,
                    )
                )
                executed_agents.append(
                    agent_name
                )
            except Exception as exc:
                error = ExecutionError.from_exception(
                    agent_name=agent_name,
                    exception=exc,
                )
                errors.append(
                    CFOExecutionError(
                        agent_name=error.agent_name,
                        message=error.message,
                        exception_type=(
                            error.exception_type
                        ),
                        category=error.category,
                        provider_status_code=(
                            error.provider_status_code
                        ),
                        retryable=error.retryable,
                    )
                )
                break

        status = (
            HybridRuntimeStatus.COMPLETED
            if not errors
            else (
                HybridRuntimeStatus.PARTIAL
                if executed_agents
                else HybridRuntimeStatus.FAILED
            )
        )
        final_agent = (
            executed_agents[-1]
            if executed_agents
            else None
        )

        return CFOAnalysisResponse(
            request=report_request.request,
            correlation_id=report_request.correlation_id,
            status=status,
            execution_plan=list(
                _COMPANY_REPORT_PLAN
            ),
            executed_agents=executed_agents,
            verified_results=verified_results,
            ai_results=ai_results,
            final_agent=final_agent,
            final_output=(
                ai_results.get(
                    final_agent
                )
                if final_agent is not None
                else None
            ),
            errors=errors,
        )

    @staticmethod
    def _insufficient_data_response(
        *,
        report_request: CompanyCFOReportRequest,
        verified_results: dict[str, Any],
    ) -> CFOAnalysisResponse:
        profile = verified_results[
            "data_profile"
        ]
        final_output = {
            "report_status": "INSUFFICIENT_DATA",
            "summary": (
                "The monthly aggregation is available, but the "
                "verified evidence threshold for company-wide Risk, "
                "Forecast, Strategy, and Chief CFO analysis was not met."
            ),
            "verified_capabilities": profile[
                "verified_capabilities"
            ],
            "limitations": profile[
                "limitations"
            ],
        }

        return CFOAnalysisResponse(
            request=report_request.request,
            correlation_id=report_request.correlation_id,
            status=HybridRuntimeStatus.COMPLETED,
            execution_plan=[],
            executed_agents=[],
            verified_results=verified_results,
            ai_results={},
            final_agent="deterministic_aggregation",
            final_output=final_output,
            errors=[],
        )
