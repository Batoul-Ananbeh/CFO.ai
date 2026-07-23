"""FastAPI application factory for CFO.ai."""

from __future__ import annotations

from fastapi import FastAPI, status

from src.api.history_routes import (
    router as history_router,
)
from src.api.models import HealthResponse
from src.api.routes import (
    router as analysis_router,
)
from src.application.service import (
    CFOApplicationService,
)


API_VERSION = "1.0.0"


def create_app(
    *,
    service: CFOApplicationService | None = None,
) -> FastAPI:
    """
    Create the CFO.ai FastAPI application.

    A service may be injected for tests or embedded deployments.
    When omitted, the API creates the production service lazily on
    the first analysis request.
    """

    app = FastAPI(
        title="CFO.ai API",
        description=(
            "Deterministic financial workflows combined with "
            "dynamic specialized AI agents and persistent "
            "financial analysis history."
        ),
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    if service is not None:
        app.state.cfo_service = service

    @app.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        tags=["System"],
    )
    def health_check() -> HealthResponse:
        """Return a lightweight service health response."""

        return HealthResponse(
            status="ok",
            service="CFO.ai",
            api_version=API_VERSION,
        )

    app.include_router(
        analysis_router
    )

    app.include_router(
        history_router
    )

    return app