"""Regression tests for MVP reliability and operational readiness."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from src.ai.provider import LLMProvider
from src.api.app import create_app
from src.application.factory import build_cfo_application_service
from src.application.models import CFOAnalysisResponse
from src.database.repositories.errors import DuplicateRecordError
from src.database.readiness import DatabaseReadiness
from src.database.base import Base
from src.database.session import (
    create_database_engine,
    create_session_factory,
)
from src.database.settings import DatabaseSettings
import src.database.models  # noqa: F401
from tests.test_cfo_api import FakeAPIProvider, valid_transaction


class DuplicatePreflightPersistence:
    """Reject a known correlation ID before any runtime execution."""

    def ensure_correlation_id_available(
        self,
        correlation_id: str,
    ) -> None:
        raise DuplicateRecordError(
            f"Analysis correlation ID {correlation_id!r} already exists."
        )

    def persist(self, **_: Any) -> str:
        raise AssertionError("Duplicate preflight must skip persistence.")


class DuplicateRacePersistence:
    """Simulate a concurrent insert after preflight succeeds."""

    def ensure_correlation_id_available(
        self,
        correlation_id: str,
    ) -> None:
        return None

    def persist(self, **_: Any) -> str:
        raise DuplicateRecordError(
            "Concurrent request inserted the correlation ID first."
        )


def _request(correlation_id: str) -> dict[str, Any]:
    return {
        "request": "Explain the journal entry",
        "financial_input": valid_transaction(),
        "metadata": {
            "correlation_id": correlation_id,
        },
    }


def _client(
    *,
    provider: LLMProvider,
    persistence: Any,
) -> TestClient:
    service = build_cfo_application_service(
        provider=provider,
        persistence=persistence,
    )
    return TestClient(create_app(service=service))


def test_duplicate_preflight_returns_409_without_ai_execution():
    provider = FakeAPIProvider()
    client = _client(
        provider=provider,
        persistence=DuplicatePreflightPersistence(),
    )

    response = client.post(
        "/api/v1/analyses",
        json=_request("CORR-DUPLICATE-PREFLIGHT"),
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "DUPLICATE_CORRELATION_ID",
        "message": (
            "An analysis with this correlation ID already exists."
        ),
        "correlation_id": "CORR-DUPLICATE-PREFLIGHT",
    }
    assert provider.requests == []


def test_real_persistence_rejects_duplicate_before_second_ai_call():
    engine = create_database_engine(
        DatabaseSettings(
            url="sqlite+pysqlite:///:memory:",
        )
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    provider = FakeAPIProvider()
    service = build_cfo_application_service(
        provider=provider,
        persistence_enabled=True,
        session_factory=session_factory,
    )
    client = TestClient(create_app(service=service))
    request = _request("CORR-DUPLICATE-REAL-PERSISTENCE")

    first_response = client.post(
        "/api/v1/analyses",
        json=request,
    )
    second_response = client.post(
        "/api/v1/analyses",
        json=request,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert len(provider.requests) == 1

    engine.dispose()


def test_duplicate_race_returns_409_after_database_protection():
    provider = FakeAPIProvider()
    client = _client(
        provider=provider,
        persistence=DuplicateRacePersistence(),
    )

    response = client.post(
        "/api/v1/analyses",
        json=_request("CORR-DUPLICATE-RACE"),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_CORRELATION_ID"
    assert len(provider.requests) == 1


def test_public_validation_error_hides_internal_pydantic_details():
    provider = FakeAPIProvider()
    client = _client(
        provider=provider,
        persistence=None,
    )
    transaction = valid_transaction()
    transaction["amount"]["amount"] = "-1.00"

    response = client.post(
        "/api/v1/analyses",
        json={
            "request": "Explain the journal entry",
            "financial_input": transaction,
        },
    )

    assert response.status_code == 422
    error = response.json()["errors"][0]
    assert error["category"] == "VALIDATION"
    assert error["message"] == (
        "Financial input failed validation. Verify required fields, "
        "positive amounts, currencies, and debit/credit account mappings."
    )
    assert "pydantic.dev" not in error["message"]
    assert provider.requests == []


def test_readiness_returns_200_when_database_and_ai_are_ready(
    monkeypatch,
):
    import src.api.app as app_module

    monkeypatch.setattr(
        app_module,
        "check_database_readiness",
        lambda engine: DatabaseReadiness(
            ready=True,
            connection_ok=True,
            current_revision="20260723_0002",
            head_revision="20260723_0002",
            tables=("companies",),
            missing_tables=(),
            detail="Database schema is ready.",
        ),
    )
    monkeypatch.setattr(
        app_module,
        "get_engine",
        lambda: object(),
    )
    monkeypatch.setattr(
        app_module.AISettings,
        "from_env",
        classmethod(
            lambda cls: SimpleNamespace(
                validate=lambda: None
            )
        ),
    )

    response = TestClient(
        create_app(
            service=build_cfo_application_service(
                provider=FakeAPIProvider()
            )
        )
    ).get("/readiness")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_returns_503_without_exposing_secrets(
    monkeypatch,
):
    import src.api.app as app_module

    monkeypatch.setattr(
        app_module,
        "check_database_readiness",
        lambda engine: DatabaseReadiness(
            ready=False,
            connection_ok=True,
            current_revision="20260723_0001",
            head_revision="20260723_0002",
            tables=("companies",),
            missing_tables=("staging_records",),
            detail=(
                "Missing tables: staging_records. Database revision "
                "20260723_0001 does not match head 20260723_0002."
            ),
        ),
    )
    monkeypatch.setattr(
        app_module,
        "get_engine",
        lambda: object(),
    )

    class InvalidSettings:
        def validate(self) -> None:
            raise ValueError("Secret value must never be returned.")

    monkeypatch.setattr(
        app_module.AISettings,
        "from_env",
        classmethod(lambda cls: InvalidSettings()),
    )

    response = TestClient(create_app()).get("/readiness")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["components"]["database"]["status"] == "not_ready"
    assert payload["components"]["ai"] == {
        "status": "not_ready",
        "detail": "AI provider configuration is incomplete.",
    }
    assert "Secret value" not in response.text
