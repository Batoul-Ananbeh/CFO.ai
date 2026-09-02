"""HTTP routes for CFO.ai."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import JSONResponse

from src.api.dependencies import get_cfo_service
from src.api.models import (
    APIConflictResponse,
    AgentCatalogResponse,
    AgentDescriptor,
)
from src.application.models import (
    CFOAnalysisRequest,
    CFOAnalysisResponse,
)
from src.application.service import (
    CFOApplicationService,
)
from src.orchestrator.errors import (
    ExecutionErrorCategory,
)
from src.planning.dependency_resolver import (
    AGENT_DEPENDENCIES,
    CANONICAL_AGENT_ORDER,
)
from src.runtime.models import (
    HybridRuntimeStatus,
)
from src.database.repositories.errors import (
    DuplicateRecordError,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["CFO Analysis"],
)


_PUBLIC_VALIDATION_MESSAGE = (
    "Financial input failed validation. Verify required fields, positive "
    "amounts, currencies, and debit/credit account mappings."
)


def _public_failure_response(
    response: CFOAnalysisResponse,
) -> CFOAnalysisResponse:
    """Remove internal validation details from the public API response."""

    public_errors = [
        error.model_copy(
            update={
                "message": (
                    _PUBLIC_VALIDATION_MESSAGE
                    if error.category
                    is ExecutionErrorCategory.VALIDATION
                    else error.message
                )
            }
        )
        for error in response.errors
    ]

    return response.model_copy(
        update={"errors": public_errors}
    )


def _resolve_failure_status(
    response: CFOAnalysisResponse,
) -> int:
    """
    Map structured CFO execution errors to an HTTP status code.

    Priority:
    - Invalid financial input: 422
    - AI provider unavailable, unauthorized, or rate limited: 503
    - AI provider returned an invalid response: 502
    - Unexpected internal failures: 500
    """

    categories = {
        error.category
        for error in response.errors
    }

    if (
        ExecutionErrorCategory.VALIDATION
        in categories
    ):
        return (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    unavailable_categories = {
        ExecutionErrorCategory.AI_AUTHENTICATION,
        ExecutionErrorCategory.AI_RATE_LIMIT,
        ExecutionErrorCategory.AI_PROVIDER_UNAVAILABLE,
    }

    if categories.intersection(
        unavailable_categories
    ):
        return status.HTTP_503_SERVICE_UNAVAILABLE

    provider_failure_categories = {
        ExecutionErrorCategory.AI_PROVIDER,
        ExecutionErrorCategory.AI_PROVIDER_RESPONSE,
    }

    if categories.intersection(
        provider_failure_categories
    ):
        return status.HTTP_502_BAD_GATEWAY

    return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get(
    "/agents",
    response_model=AgentCatalogResponse,
    status_code=status.HTTP_200_OK,
)
def list_available_agents() -> AgentCatalogResponse:
    """Return the dynamic CFO agent catalog."""

    agents = [
        AgentDescriptor(
            name=agent_name,
            dependencies=list(
                AGENT_DEPENDENCIES[agent_name]
            ),
        )
        for agent_name in CANONICAL_AGENT_ORDER
    ]

    return AgentCatalogResponse(
        agents=agents,
        total=len(agents),
    )


@router.post(
    "/analyses",
    response_model=CFOAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": CFOAnalysisResponse,
            "description": (
                "The financial input failed deterministic "
                "validation."
            ),
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": CFOAnalysisResponse,
            "description": (
                "The AI provider returned an invalid or "
                "unsuccessful response."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": CFOAnalysisResponse,
            "description": (
                "The AI provider is unavailable, rate limited, "
                "or not configured correctly."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": CFOAnalysisResponse,
            "description": (
                "An unexpected internal execution error occurred."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": APIConflictResponse,
            "description": (
                "The correlation ID already belongs to a persisted analysis."
            ),
        },
    },
)
def create_financial_analysis(
    analysis_request: CFOAnalysisRequest,
    service: Annotated[
        CFOApplicationService,
        Depends(get_cfo_service),
    ],
) -> CFOAnalysisResponse | JSONResponse:
    """
    Run deterministic financial validation and selected AI agents.

    Successful and partially completed executions return HTTP 200.

    Failed executions return a status code based on the structured
    execution error category.
    """

    try:
        response = service.analyze(
            analysis_request
        )
    except DuplicateRecordError:
        correlation_id = analysis_request.metadata.get(
            "correlation_id"
        )

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=APIConflictResponse(
                code="DUPLICATE_CORRELATION_ID",
                message=(
                    "An analysis with this correlation ID already exists."
                ),
                correlation_id=(
                    correlation_id
                    if isinstance(correlation_id, str)
                    else "UNKNOWN"
                ),
            ).model_dump(mode="json"),
        )

    if response.status is HybridRuntimeStatus.FAILED:
        public_response = _public_failure_response(
            response
        )

        return JSONResponse(
            status_code=_resolve_failure_status(
                response
            ),
            content=public_response.model_dump(
                mode="json"
            ),
        )

    return response
