"""Public FastAPI interface for CFO.ai."""

from src.api.app import API_VERSION, create_app


__all__ = [
    "API_VERSION",
    "create_app",
]
