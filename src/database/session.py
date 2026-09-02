"""SQLAlchemy engine and session management for CFO.ai."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import TypeAlias

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.settings import DatabaseSettings


SessionFactory: TypeAlias = sessionmaker[Session]


def create_database_engine(
    settings: DatabaseSettings | None = None,
) -> Engine:
    """Create a SQLAlchemy engine without opening a connection."""

    selected_settings = (
        settings
        if settings is not None
        else DatabaseSettings.from_env()
    )

    selected_settings.validate()

    common_options: dict[str, object] = {
        "echo": selected_settings.echo,
        "pool_pre_ping": True,
    }

    if selected_settings.is_sqlite:
        common_options["connect_args"] = {
            "check_same_thread": False,
        }

        if ":memory:" in selected_settings.url:
            common_options["poolclass"] = StaticPool

    else:
        common_options.update(
            {
                "pool_size": (
                    selected_settings.pool_size
                ),
                "max_overflow": (
                    selected_settings.max_overflow
                ),
                "pool_timeout": (
                    selected_settings.pool_timeout
                ),
                "pool_recycle": (
                    selected_settings.pool_recycle
                ),
            }
        )

    return create_engine(
        selected_settings.url,
        **common_options,
    )


def create_session_factory(
    engine: Engine,
) -> SessionFactory:
    """Create a reusable SQLAlchemy session factory."""

    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Return cached environment-backed database settings."""

    settings = DatabaseSettings.from_env()
    settings.validate()

    return settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine."""

    return create_database_engine(
        get_database_settings()
    )


@lru_cache(maxsize=1)
def get_session_factory() -> SessionFactory:
    """Return the process-wide SQLAlchemy session factory."""

    return create_session_factory(
        get_engine()
    )


@contextmanager
def session_scope(
    session_factory: SessionFactory | None = None,
) -> Iterator[Session]:
    """
    Provide a transactional SQLAlchemy session.

    Successful execution commits the transaction. Exceptions trigger
    rollback before the session is closed.
    """

    selected_factory = (
        session_factory
        if session_factory is not None
        else get_session_factory()
    )

    session = selected_factory()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
