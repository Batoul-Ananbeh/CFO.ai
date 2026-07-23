"""Repository exceptions for CFO.ai persistence."""

from __future__ import annotations


class PersistenceError(RuntimeError):
    """Base exception for persistence-layer failures."""


class RecordNotFoundError(PersistenceError):
    """Raised when a required database record does not exist."""


class DuplicateRecordError(PersistenceError):
    """Raised when a unique database record already exists."""