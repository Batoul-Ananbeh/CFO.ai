"""FastAPI application factory for CFO.ai."""

from __future__ import annotations

from fastapi import FastAPI, Response, status

from src.api.history_routes import (
    router as history_router,
)
from src.api.ingestion_routes import (
    router as ingestion_router,
)
from src.ai.settings import AISettings
from src.api.models import (
    HealthResponse,
    ReadinessComponent,
    ReadinessResponse,
)
from src.api.routes import (
    router as analysis_router,
)
from src.application.service import (
    CFOApplicationService,
)
from src.database.readiness import (
    check_database_readiness,
)
from src.database.session import get_engine


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

    @app.get(
        "/readiness",
        response_model=ReadinessResponse,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "model": ReadinessResponse,
                "description": (
                    "One or more required components are not ready."
                ),
            }
        },
        tags=["System"],
    )
    def readiness_check(
        response: Response,
    ) -> ReadinessResponse:
        """Check database schema and AI configuration without exposing secrets."""

        database_result = check_database_readiness(
            get_engine()
        )

        try:
            AISettings.from_env().validate()
            ai_ready = True
            ai_detail = "AI provider configuration is present."
        except Exception:
            ai_ready = False
            ai_detail = "AI provider configuration is incomplete."

        overall_ready = database_result.ready and ai_ready

        if not overall_ready:
            response.status_code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return ReadinessResponse(
            status=(
                "ready"
                if overall_ready
                else "not_ready"
            ),
            service="CFO.ai",
            components={
                "database": ReadinessComponent(
                    status=(
                        "ready"
                        if database_result.ready
                        else "not_ready"
                    ),
                    detail=database_result.detail,
                ),
                "ai": ReadinessComponent(
                    status=(
                        "ready"
                        if ai_ready
                        else "not_ready"
                    ),
                    detail=ai_detail,
                ),
            },
        )

    app.include_router(
        analysis_router
    )

    app.include_router(
        history_router
    )

    app.include_router(
        ingestion_router
    )

    return app
