"""Application request and response models for CFO.ai."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    WithJsonSchema,
    field_validator,
)

from src.orchestrator.errors import (
    ExecutionErrorCategory,
)
from src.runtime.models import (
    HybridRuntimeResult,
    HybridRuntimeStatus,
)
from src.schemas.general_ledger import (
    LedgerTransactionInput,
)


FinancialInputPayload = Annotated[
    dict[str, Any],
    WithJsonSchema(
        LedgerTransactionInput.model_json_schema(),
        mode="validation",
    ),
]


class CFOAnalysisRequest(BaseModel):
    """Validated application request for one CFO analysis."""

    model_config = ConfigDict(
        extra="forbid",
    )

    request: str = Field(
        min_length=1,
    )

    financial_input: FinancialInputPayload = Field(
        min_length=1,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("request")
    @classmethod
    def normalize_request(
        cls,
        value: str,
    ) -> str:
        """Strip surrounding whitespace from the request."""

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "Request cannot be empty."
            )

        return normalized_value


class CFOExecutionError(BaseModel):
    """API-friendly representation of an execution error."""

    model_config = ConfigDict(
        extra="forbid",
    )

    agent_name: str
    message: str
    exception_type: str

    category: ExecutionErrorCategory
    provider_status_code: int | None = None
    retryable: bool = False


class CFOAnalysisResponse(BaseModel):
    """Unified application response from CFO.ai."""

    model_config = ConfigDict(
        extra="forbid",
    )

    request: str

    analysis_id: str | None = None
    correlation_id: str | None = None

    status: HybridRuntimeStatus

    execution_plan: list[str] = Field(
        default_factory=list,
    )

    executed_agents: list[str] = Field(
        default_factory=list,
    )

    verified_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    ai_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    final_agent: str | None = None
    final_output: dict[str, Any] | None = None

    errors: list[CFOExecutionError] = Field(
        default_factory=list,
    )

    @classmethod
    def from_runtime_result(
        cls,
        result: HybridRuntimeResult,
    ) -> "CFOAnalysisResponse":
        """Create an application response from a runtime result."""

        payload = result.to_dict()

        verified_results = payload[
            "verified_results"
        ]

        workflow_result = verified_results.get(
            "gl_controller_workflow",
            {},
        )

        correlation_id: str | None = None

        if isinstance(
            workflow_result,
            dict,
        ):
            raw_correlation_id = workflow_result.get(
                "correlation_id"
            )

            if isinstance(
                raw_correlation_id,
                str,
            ):
                correlation_id = raw_correlation_id

        executed_agents = list(
            payload["executed_agents"]
        )

        final_agent = (
            executed_agents[-1]
            if executed_agents
            else None
        )

        final_output: dict[str, Any] | None = None

        if final_agent is not None:
            raw_final_output = payload[
                "ai_results"
            ].get(final_agent)

            if isinstance(
                raw_final_output,
                dict,
            ):
                final_output = raw_final_output

            elif raw_final_output is not None:
                final_output = {
                    "result": raw_final_output,
                }

        return cls(
            request=payload["request"],
            correlation_id=correlation_id,
            status=HybridRuntimeStatus(
                payload["status"]
            ),
            execution_plan=list(
                payload["execution_plan"]
            ),
            executed_agents=executed_agents,
            verified_results=verified_results,
            ai_results=payload["ai_results"],
            final_agent=final_agent,
            final_output=final_output,
            errors=[
                CFOExecutionError.model_validate(
                    error
                )
                for error in payload["errors"]
            ],
        )