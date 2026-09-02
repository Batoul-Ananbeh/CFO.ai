"""Company repository for CFO.ai."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import Company
from src.database.repositories.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
)


class CompanyRepository:
    """Persist and query CFO.ai companies."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        *,
        code: str,
        name: str,
        base_currency: str = "JOD",
        is_active: bool = True,
    ) -> Company:
        """Create and flush a company record."""

        company = Company(
            code=self._normalize_code(code),
            name=self._normalize_required_text(
                name,
                field_name="Company name",
            ),
            base_currency=(
                self._normalize_currency(
                    base_currency
                )
            ),
            is_active=is_active,
        )

        self._session.add(company)

        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateRecordError(
                f"Company code {company.code!r} already exists."
            ) from exc

        return company

    def get_by_id(
        self,
        company_id: str,
    ) -> Company | None:
        """Return a company by primary key."""

        return self._session.get(
            Company,
            company_id,
        )

    def require_by_id(
        self,
        company_id: str,
    ) -> Company:
        """Return a company or raise a structured error."""

        company = self.get_by_id(
            company_id
        )

        if company is None:
            raise RecordNotFoundError(
                f"Company {company_id!r} was not found."
            )

        return company

    def get_by_code(
        self,
        code: str,
    ) -> Company | None:
        """Return a company by its business code."""

        statement = select(Company).where(
            Company.code
            == self._normalize_code(code)
        )

        return self._session.scalar(
            statement
        )

    def list_active(self) -> list[Company]:
        """Return active companies ordered by name."""

        statement = (
            select(Company)
            .where(
                Company.is_active.is_(True)
            )
            .order_by(
                Company.name.asc()
            )
        )

        return list(
            self._session.scalars(
                statement
            )
        )

    @staticmethod
    def _normalize_code(
        value: str,
    ) -> str:
        """Normalize a company business code."""

        return CompanyRepository._normalize_required_text(
            value,
            field_name="Company code",
        ).upper()

    @staticmethod
    def _normalize_currency(
        value: str,
    ) -> str:
        """Normalize an ISO-style currency code."""

        normalized_value = (
            CompanyRepository._normalize_required_text(
                value,
                field_name="Base currency",
            ).upper()
        )

        if len(normalized_value) != 3:
            raise ValueError(
                "Base currency must contain exactly 3 characters."
            )

        return normalized_value

    @staticmethod
    def _normalize_required_text(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """Normalize required text input."""

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized_value