"""Persistent company CFO reports built from verified monthly aggregation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

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
from src.ingestion.report_context import (
    build_company_report_context,
)
from src.orchestrator.errors import (
    ExecutionError,
)
from src.runtime.models import (
    HybridRuntimeStatus,
)


CompanyReportExecutionMode = Literal[
    "economy",
    "balanced",
    "full",
]

_COMPANY_REPORT_PLANS: dict[
    CompanyReportExecutionMode,
    list[str],
] = {
    "economy": [
        "risk_ai",
        "chief_cfo_ai",
    ],
    "balanced": [
        "risk_ai",
        "forecast_ai",
        "chief_cfo_ai",
    ],
    "full": [
        "risk_ai",
        "forecast_ai",
        "strategy_ai",
        "chief_cfo_ai",
    ],
}

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
    execution_mode: CompanyReportExecutionMode = "economy"


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
                    "ai_execution_mode": (
                        report_request.execution_mode
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
        execution_plan = _COMPANY_REPORT_PLANS[
            report_request.execution_mode
        ]
        base_context = build_company_report_context(
            verified_results["monthly_aggregation"]
        )
        available_agents = {
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
        }
        agents_by_name = {
            agent_name: (agent, method_name)
            for agent_name, agent, method_name in available_agents
        }

        for agent_name in execution_plan:
            agent, method_name = agents_by_name[
                agent_name
            ]
            context = {
                **base_context,
                "specialized_agent_results": dict(
                    ai_results
                ),
                "execution_policy": {
                    "mode": report_request.execution_mode,
                    "planned_agents": execution_plan,
                    "omitted_agents": [
                        name
                        for name in _COMPANY_REPORT_PLANS["full"]
                        if name not in execution_plan
                    ],
                },
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
        verified_results["ai_cost_policy"] = {
            "execution_mode": report_request.execution_mode,
            "planned_ai_calls": len(execution_plan),
            "executed_ai_calls": len(executed_agents),
            "full_report_ai_calls": len(
                _COMPANY_REPORT_PLANS["full"]
            ),
            "mode_avoided_ai_calls": (
                len(_COMPANY_REPORT_PLANS["full"])
                - len(execution_plan)
            ),
            "unexecuted_planned_ai_calls": (
                len(execution_plan)
                - len(executed_agents)
            ),
            "usage": self._usage_summary(ai_results),
            "context_policy": (
                base_context["context_policy"]["name"]
            ),
        }

        return CFOAnalysisResponse(
            request=report_request.request,
            correlation_id=report_request.correlation_id,
            status=status,
            execution_plan=list(
                execution_plan
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
    def _usage_summary(
        ai_results: dict[str, Any],
    ) -> dict[str, int | None]:
        fields = (
            "prompt_tokens",
            "output_tokens",
            "total_tokens",
            "cached_tokens",
            "thought_tokens",
        )
        totals = {
            field: 0
            for field in fields
        }
        observed = {
            field: False
            for field in fields
        }

        for result in ai_results.values():
            metadata = (
                result.get("_ai_metadata")
                if isinstance(result, dict)
                else None
            )
            usage = (
                metadata.get("usage")
                if isinstance(metadata, dict)
                else None
            )

            if not isinstance(usage, dict):
                continue

            for field in fields:
                value = usage.get(field)

                if isinstance(value, int) and not isinstance(
                    value,
                    bool,
                ):
                    totals[field] += value
                    observed[field] = True

        return {
            field: (
                totals[field]
                if observed[field]
                else None
            )
            for field in fields
        }

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
