"""Transactional unit of work for CFO.ai persistence."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session

from src.database.repositories import (
    AgentExecutionRepository,
    AnalysisRepository,
    AuditLogRepository,
    BranchRepository,
    CompanyRepository,
)
from src.database.session import (
    SessionFactory,
    get_session_factory,
)


class PersistenceUnitOfWork:
    """Coordinate repositories inside one database transaction."""

    def __init__(
        self,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._session_factory = (
            session_factory
            if session_factory is not None
            else get_session_factory()
        )

        self.session: Session | None = None

        self.companies: CompanyRepository
        self.branches: BranchRepository
        self.analyses: AnalysisRepository
        self.agent_executions: AgentExecutionRepository
        self.audit_logs: AuditLogRepository

    def __enter__(
        self,
    ) -> "PersistenceUnitOfWork":
        """Open a database session and repositories."""

        self.session = self._session_factory()

        self.companies = CompanyRepository(
            self.session
        )

        self.branches = BranchRepository(
            self.session
        )

        self.analyses = AnalysisRepository(
            self.session
        )

        self.agent_executions = (
            AgentExecutionRepository(
                self.session
            )
        )

        self.audit_logs = AuditLogRepository(
            self.session
        )

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Commit successful work or roll back failures."""

        try:
            if exception_type is None:
                self.commit()
            else:
                self.rollback()

        finally:
            self.close()

        return False

    def commit(self) -> None:
        """Commit the active database transaction."""

        session = self._require_session()

        try:
            session.commit()
        except Exception:
            session.rollback()
            raise

    def rollback(self) -> None:
        """Roll back the active database transaction."""

        self._require_session().rollback()

    def close(self) -> None:
        """Close the active database session."""

        if self.session is not None:
            self.session.close()
            self.session = None

    def _require_session(self) -> Session:
        """Return the active session or fail clearly."""

        if self.session is None:
            raise RuntimeError(
                "The persistence unit of work is not active."
            )

        return self.session