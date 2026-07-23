"""Verify the live CFO.ai PostgreSQL database."""

from __future__ import annotations

from sqlalchemy import inspect, text

from src.database.session import (
    create_database_engine,
)
from src.database.settings import (
    DatabaseSettings,
)


EXPECTED_TABLES = {
    "companies",
    "branches",
    "analyses",
    "agent_executions",
    "audit_logs",
    "alembic_version",
}


def main() -> None:
    """Connect to PostgreSQL and verify the migrated schema."""

    settings = DatabaseSettings.from_env()
    settings.validate()

    print("=== CFO.ai Database Check ===")
    print(f"Database: {settings.safe_url}")

    engine = create_database_engine(
        settings
    )

    try:
        with engine.connect() as connection:
            result = connection.scalar(
                text("SELECT 1")
            )

        table_names = set(
            inspect(engine).get_table_names()
        )

        print(f"Connection result: {result}")
        print("Tables:")

        for table_name in sorted(
            table_names
        ):
            print(f"- {table_name}")

        missing_tables = (
            EXPECTED_TABLES - table_names
        )

        if missing_tables:
            raise RuntimeError(
                "Missing expected tables: "
                + ", ".join(
                    sorted(missing_tables)
                )
            )

        print("Database schema is ready.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
