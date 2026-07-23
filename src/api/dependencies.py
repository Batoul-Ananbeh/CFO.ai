"""FastAPI dependencies for CFO.ai."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import (
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from src.application.factory import (
    build_cfo_application_service,
)
from src.application.service import (
    CFOApplicationService,
)
from src.database.session import (
    get_session_factory,
)


def get_cfo_service(
    request: Request,
) -> CFOApplicationService:
    """
    Return the configured CFO application service.

    Tests and embedded applications may inject a prepared service
    into app.state. Production execution builds the service lazily
    with PostgreSQL persistence enabled.
    """

    existing_service = getattr(
        request.app.state,
        "cfo_service",
        None,
    )

    if existing_service is not None:
        if not isinstance(
            existing_service,
            CFOApplicationService,
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "The configured CFO service has an invalid type."
                ),
            )

        return existing_service

    try:
        created_service = (
            build_cfo_application_service(
                persistence_enabled=True
            )
        )

    except Exception as exception:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "CFO.ai is not configured for live execution. "
                "Verify AI and database settings."
            ),
        ) from exception

    request.app.state.cfo_service = created_service

    return created_service


def get_database_session() -> Iterator[Session]:
    """Provide one SQLAlchemy session to a read API request."""

    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session

    finally:
        session.close()