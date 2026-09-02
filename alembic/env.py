"""Alembic environment configuration for CFO.ai."""

from __future__ import annotations

from alembic import context

from src.database.base import Base
from src.database.session import create_database_engine
from src.database.settings import DatabaseSettings

import src.database.models  # noqa: F401


config = context.config

settings = DatabaseSettings.from_env()
settings.validate()

config.set_main_option(
    "sqlalchemy.url",
    settings.url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""

    context.configure(
        url=settings.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
        render_as_batch=settings.is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    engine = create_database_engine(
        settings
    )

    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                render_as_batch=settings.is_sqlite,
            )

            with context.begin_transaction():
                context.run_migrations()

    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
