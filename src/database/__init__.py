"""Public database interfaces for CFO.ai."""

from src.database.base import Base
from src.database.models import (
    AgentExecutionRecord,
    AnalysisRecord,
    AuditLogRecord,
    Branch,
    Company,
    IngestionBatch,
    IngestionSourceFile,
    StagingRecord,
)
from src.database.repositories import (
    AgentExecutionRepository,
    AnalysisRepository,
    AuditLogRepository,
    BranchRepository,
    CompanyRepository,
    DuplicateRecordError,
    IngestionRepository,
    PersistenceError,
    RecordNotFoundError,
)
from src.database.session import (
    SessionFactory,
    create_database_engine,
    create_session_factory,
    get_database_settings,
    get_engine,
    get_session_factory,
    session_scope,
)
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


__all__ = [
    "AgentExecutionRecord",
    "AgentExecutionRepository",
    "AnalysisRecord",
    "AnalysisRepository",
    "AuditLogRecord",
    "AuditLogRepository",
    "Base",
    "Branch",
    "BranchRepository",
    "Company",
    "CompanyRepository",
    "IngestionBatch",
    "IngestionSourceFile",
    "IngestionRepository",
    "DatabaseSettings",
    "DuplicateRecordError",
    "PersistenceError",
    "PersistenceUnitOfWork",
    "RecordNotFoundError",
    "SessionFactory",
    "StagingRecord",
    "create_database_engine",
    "create_session_factory",
    "get_database_settings",
    "get_engine",
    "get_session_factory",
    "session_scope",
]
