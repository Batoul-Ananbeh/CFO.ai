"""Database foundation tests for CFO.ai."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from src.database.session import (
    create_database_engine,
    create_session_factory,
    session_scope,
)
from src.database.settings import DatabaseSettings


def sqlite_settings() -> DatabaseSettings:
    """Return isolated in-memory database settings."""

    return DatabaseSettings(
        url="sqlite+pysqlite:///:memory:",
        echo=False,
    )


def test_database_settings_validate_sqlite():
    settings = sqlite_settings()

    settings.validate()

    assert settings.is_sqlite is True
    assert settings.safe_url == (
        "sqlite+pysqlite:///:memory:"
    )


def test_database_engine_executes_query():
    engine = create_database_engine(
        sqlite_settings()
    )

    session_factory = create_session_factory(
        engine
    )

    with session_factory() as session:
        result = session.scalar(
            text("SELECT 1")
        )

    assert result == 1

    engine.dispose()


def test_session_scope_commits_transaction():
    engine = create_database_engine(
        sqlite_settings()
    )

    session_factory = create_session_factory(
        engine
    )

    with session_scope(session_factory) as session:
        session.execute(
            text(
                """
                CREATE TABLE test_records (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
                """
            )
        )

        session.execute(
            text(
                """
                INSERT INTO test_records (id, name)
                VALUES (1, 'CFO.ai')
                """
            )
        )

    with session_factory() as session:
        stored_name = session.scalar(
            text(
                """
                SELECT name
                FROM test_records
                WHERE id = 1
                """
            )
        )

    assert stored_name == "CFO.ai"

    engine.dispose()


def test_session_scope_rolls_back_transaction():
    engine = create_database_engine(
        sqlite_settings()
    )

    session_factory = create_session_factory(
        engine
    )

    with session_scope(session_factory) as session:
        session.execute(
            text(
                """
                CREATE TABLE rollback_records (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
                """
            )
        )

    with pytest.raises(
        RuntimeError,
        match="Force rollback",
    ):
        with session_scope(
            session_factory
        ) as session:
            session.execute(
                text(
                    """
                    INSERT INTO rollback_records (id, name)
                    VALUES (1, 'Rollback')
                    """
                )
            )

            raise RuntimeError(
                "Force rollback"
            )

    with session_factory() as session:
        record_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM rollback_records
                """
            )
        )

    assert record_count == 0

    engine.dispose()
