"""Utilities for safely moving verified data between AI agents."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel

from src.ai.provider import LLMProvider


def to_json_compatible(value: Any) -> Any:
    """Convert CFO.ai values into JSON-compatible structures."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            str(key): to_json_compatible(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            to_json_compatible(item)
            for item in value
        ]

    return value


def get_context_result(
    context: Any,
    result_name: str,
) -> Any:
    """Read one result from an ExecutionContext-compatible object."""

    if hasattr(context, "get_result"):
        return context.get_result(result_name)

    results = getattr(context, "results", None)

    if isinstance(results, dict):
        return results.get(result_name)

    raise TypeError(
        "Context must provide get_result() or a results dictionary."
    )


def build_verified_agent_context(
    context: Any,
    source_result_names: tuple[str, ...],
) -> dict[str, Any]:
    """Build verified context for one specialized AI agent."""

    selected_results = {
        result_name: to_json_compatible(
            get_context_result(
                context,
                result_name,
            )
        )
        for result_name in source_result_names
    }

    metadata = to_json_compatible(
        getattr(
            context,
            "metadata",
            {},
        )
    )

    request = getattr(
        context,
        "request",
        None,
    )

    return {
        "original_request": request,
        "metadata": metadata,
        "agent_results": selected_results,
    }


def attach_ai_metadata(
    result: Any,
    provider: LLMProvider,
) -> dict[str, Any]:
    """Attach provider telemetry to a serialized agent result."""

    payload = to_json_compatible(result)

    if not isinstance(payload, dict):
        payload = {
            "result": payload,
        }

    provider_metadata = provider.last_call_metadata

    if provider_metadata is not None:
        payload["_ai_metadata"] = to_json_compatible(
            provider_metadata
        )

    return payload
