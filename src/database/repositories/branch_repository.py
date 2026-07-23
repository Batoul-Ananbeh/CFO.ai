"""Branch repository for CFO.ai."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import Branch
from src.database.repositories.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
)


class BranchRepository:
    """Persist and query company branches."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        *,
        company_id: str,
        code: str,
        name: str,
        external_reference: str | None = None,
        is_active: bool = True,
    ) -> Branch:
        """Create and flush a branch record."""

        branch = Branch(
            company_id=self._normalize_required_text(
                company_id,
                field_name="Company ID",
            ),
            code=self._normalize_code(
                code
            ),
            name=self._normalize_required_text(
                name,
                field_name="Branch name",
            ),
            external_reference=(
                self._normalize_optional_text(
                    external_reference
                )
            ),
            is_active=is_active,
        )

        self._session.add(branch)

        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateRecordError(
                "Branch code "
                f"{branch.code!r} already exists "
                "inside this company."
            ) from exc

        return branch

    def get_by_id(
        self,
        branch_id: str,
    ) -> Branch | None:
        """Return a branch by primary key."""

        return self._session.get(
            Branch,
            branch_id,
        )

    def require_by_id(
        self,
        branch_id: str,
    ) -> Branch:
        """Return a branch or raise a structured error."""

        branch = self.get_by_id(
            branch_id
        )

        if branch is None:
            raise RecordNotFoundError(
                f"Branch {branch_id!r} was not found."
            )

        return branch

    def get_by_company_and_code(
        self,
        *,
        company_id: str,
        code: str,
    ) -> Branch | None:
        """Return a branch by company and code."""

        statement = select(Branch).where(
            Branch.company_id
            == company_id,
            Branch.code
            == self._normalize_code(code),
        )

        return self._session.scalar(
            statement
        )

    def list_for_company(
        self,
        company_id: str,
        *,
        active_only: bool = True,
    ) -> list[Branch]:
        """Return branches belonging to one company."""

        statement = select(Branch).where(
            Branch.company_id
            == company_id
        )

        if active_only:
            statement = statement.where(
                Branch.is_active.is_(True)
            )

        statement = statement.order_by(
            Branch.name.asc()
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
        """Normalize a branch business code."""

        return BranchRepository._normalize_required_text(
            value,
            field_name="Branch code",
        ).upper()

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        """Normalize optional text input."""

        if value is None:
            return None

        normalized_value = value.strip()

        return (
            normalized_value
            if normalized_value
            else None
        )

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