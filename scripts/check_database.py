"""Verify the live CFO.ai PostgreSQL database."""

from __future__ import annotations

from src.database.readiness import (
    check_database_readiness,
)
from src.database.session import (
    create_database_engine,
)
from src.database.settings import (
    DatabaseSettings,
)


def main() -> int:
    """Connect to PostgreSQL and verify the migrated schema."""

    settings = DatabaseSettings.from_env()
    settings.validate()

    print("=== CFO.ai Database Check ===")
    print(f"Database: {settings.safe_url}")

    engine = create_database_engine(
        settings
    )

    try:
        result = check_database_readiness(
            engine
        )

        print(
            "Connection: "
            + (
                "ready"
                if result.connection_ok
                else "not ready"
            )
        )
        print(
            "Alembic: "
            f"current={result.current_revision or 'NONE'}, "
            f"head={result.head_revision or 'UNKNOWN'}"
        )
        print("Tables:")

        for table_name in sorted(
            result.tables
        ):
            print(f"- {table_name}")

        print(result.detail)
        return 0 if result.ready else 1

    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
