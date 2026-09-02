"""Shared database and migration readiness checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text


EXPECTED_TABLES = frozenset(
    {
        "companies",
        "branches",
        "analyses",
        "agent_executions",
        "audit_logs",
        "alembic_version",
        "ingestion_batches",
        "ingestion_source_files",
        "staging_records",
    }
)


@dataclass(frozen=True, slots=True)
class DatabaseReadiness:
    """Result of a non-mutating database readiness inspection."""

    ready: bool
    connection_ok: bool
    current_revision: str | None
    head_revision: str | None
    tables: tuple[str, ...]
    missing_tables: tuple[str, ...]
    detail: str


def get_migration_head() -> str:
    """Resolve the repository's current Alembic head revision."""

    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(project_root / "alembic"),
    )
    head_revision = ScriptDirectory.from_config(
        config
    ).get_current_head()

    if head_revision is None:
        raise RuntimeError("Alembic has no head revision.")

    return head_revision


def check_database_readiness(
    engine: Engine,
) -> DatabaseReadiness:
    """Check connectivity, required tables, and migration revision."""

    try:
        with engine.connect() as connection:
            connection.scalar(text("SELECT 1"))
            connection_ok = True

            table_names = set(
                inspect(connection).get_table_names()
            )

            current_revision = (
                connection.scalar(
                    text(
                        "SELECT version_num "
                        "FROM alembic_version"
                    )
                )
                if "alembic_version" in table_names
                else None
            )

        head_revision = get_migration_head()
        missing_tables = tuple(
            sorted(EXPECTED_TABLES - table_names)
        )
        revision_matches = (
            current_revision == head_revision
        )
        ready = (
            connection_ok
            and not missing_tables
            and revision_matches
        )

        detail_parts: list[str] = []

        if missing_tables:
            detail_parts.append(
                "Missing tables: "
                + ", ".join(missing_tables)
            )

        if not revision_matches:
            detail_parts.append(
                "Database revision "
                f"{current_revision or 'NONE'} does not match "
                f"head {head_revision}."
            )

        return DatabaseReadiness(
            ready=ready,
            connection_ok=connection_ok,
            current_revision=(
                str(current_revision)
                if current_revision is not None
                else None
            ),
            head_revision=head_revision,
            tables=tuple(sorted(table_names)),
            missing_tables=missing_tables,
            detail=(
                "Database schema is ready."
                if ready
                else " ".join(detail_parts)
            ),
        )

    except Exception as exception:
        return DatabaseReadiness(
            ready=False,
            connection_ok=False,
            current_revision=None,
            head_revision=None,
            tables=(),
            missing_tables=(),
            detail=(
                "Database readiness check failed: "
                f"{type(exception).__name__}."
            ),
        )
