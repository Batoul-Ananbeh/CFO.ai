"""ASGI entry point for CFO.ai."""

from src.api.app import create_app


app = create_app()
