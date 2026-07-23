"""Environment-backed database configuration for CFO.ai."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


load_dotenv()


def _read_bool(
    variable_name: str,
    default: bool,
) -> bool:
    """Read a strict boolean environment variable."""

    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip().lower()

    truthy_values = {
        "1",
        "true",
        "yes",
        "on",
    }

    falsy_values = {
        "0",
        "false",
        "no",
        "off",
    }

    if raw_value in truthy_values:
        return True

    if raw_value in falsy_values:
        return False

    raise ValueError(
        f"{variable_name} must be a valid boolean."
    )


def _read_int(
    variable_name: str,
    default: int,
) -> int:
    """Read an integer environment variable."""

    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{variable_name} must be a valid integer."
        ) from exc


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    """Configuration used to create the SQLAlchemy engine."""

    url: str = (
        "postgresql+psycopg://"
        "cfo_ai:cfo_ai_dev_password"
        "@localhost:5432/cfo_ai"
    )

    echo: bool = False

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1_800

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        """Create database settings from environment variables."""

        return cls(
            url=os.getenv(
                "DATABASE_URL",
                (
                    "postgresql+psycopg://"
                    "cfo_ai:cfo_ai_dev_password"
                    "@localhost:5432/cfo_ai"
                ),
            ).strip(),
            echo=_read_bool(
                "DATABASE_ECHO",
                False,
            ),
            pool_size=_read_int(
                "DATABASE_POOL_SIZE",
                5,
            ),
            max_overflow=_read_int(
                "DATABASE_MAX_OVERFLOW",
                10,
            ),
            pool_timeout=_read_int(
                "DATABASE_POOL_TIMEOUT",
                30,
            ),
            pool_recycle=_read_int(
                "DATABASE_POOL_RECYCLE",
                1_800,
            ),
        )

    @property
    def is_sqlite(self) -> bool:
        """Return whether the configured backend is SQLite."""

        return (
            make_url(self.url).get_backend_name()
            == "sqlite"
        )

    @property
    def safe_url(self) -> str:
        """Return the database URL without exposing its password."""

        return make_url(
            self.url
        ).render_as_string(
            hide_password=True
        )

    def validate(self) -> None:
        """Validate database settings before engine creation."""

        if not self.url:
            raise ValueError(
                "DATABASE_URL cannot be empty."
            )

        parsed_url = make_url(
            self.url
        )

        supported_backends = {
            "postgresql",
            "sqlite",
        }

        if (
            parsed_url.get_backend_name()
            not in supported_backends
        ):
            raise ValueError(
                "DATABASE_URL must use PostgreSQL or SQLite."
            )

        if self.pool_size < 1:
            raise ValueError(
                "DATABASE_POOL_SIZE must be at least 1."
            )

        if self.max_overflow < 0:
            raise ValueError(
                "DATABASE_MAX_OVERFLOW cannot be negative."
            )

        if self.pool_timeout < 1:
            raise ValueError(
                "DATABASE_POOL_TIMEOUT must be at least 1."
            )

        if self.pool_recycle < 1:
            raise ValueError(
                "DATABASE_POOL_RECYCLE must be at least 1."
            )
