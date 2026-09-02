"""Branch persistence model for CFO.ai."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Branch(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """Represent one operational branch belonging to a company."""

    __tablename__ = "branches"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_branches_company_code",
        ),
    )

    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    company: Mapped["Company"] = relationship(
        back_populates="branches",
    )

    analyses: Mapped[list["AnalysisRecord"]] = relationship(
        back_populates="branch",
        passive_deletes=True,
    )
