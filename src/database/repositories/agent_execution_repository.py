"""Agent execution repository for CFO.ai."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import AgentExecutionRecord
from src.database.repositories.errors import (
    DuplicateRecordError,
)


class AgentExecutionRepository:
    """Persist and query individual agent executions."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        *,
        analysis_id: str,
        agent_name: str,
        sequence_number: int,
        status: str,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        error_category: str | None = None,
        error_message: str | None = None,
        provider_status_code: int | None = None,
        retryable: bool = False,
        prompt_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        thought_tokens: int | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> AgentExecutionRecord:
        """Create and flush an agent execution record."""

        if sequence_number < 1:
            raise ValueError(
                "Agent sequence number must be at least 1."
            )

        normalized_agent_name = (
            self._normalize_required_text(
                agent_name,
                field_name="Agent name",
            )
        )

        normalized_status = (
            self._normalize_required_text(
                status,
                field_name="Execution status",
            ).upper()
        )

        normalized_output = (
            dict(output_payload)
            if output_payload is not None
            else None
        )

        extracted_usage = self._extract_usage(
            normalized_output
        )

        execution = AgentExecutionRecord(
            analysis_id=self._normalize_required_text(
                analysis_id,
                field_name="Analysis ID",
            ),
            agent_name=normalized_agent_name,
            sequence_number=sequence_number,
            status=normalized_status,
            input_payload=dict(
                input_payload or {}
            ),
            output_payload=normalized_output,
            error_category=error_category,
            error_message=error_message,
            provider_status_code=provider_status_code,
            retryable=retryable,
            prompt_tokens=self._resolve_token_value(
                explicit_value=prompt_tokens,
                extracted_value=extracted_usage[
                    "prompt_tokens"
                ],
            ),
            output_tokens=self._resolve_token_value(
                explicit_value=output_tokens,
                extracted_value=extracted_usage[
                    "output_tokens"
                ],
            ),
            total_tokens=self._resolve_token_value(
                explicit_value=total_tokens,
                extracted_value=extracted_usage[
                    "total_tokens"
                ],
            ),
            thought_tokens=self._resolve_token_value(
                explicit_value=thought_tokens,
                extracted_value=extracted_usage[
                    "thought_tokens"
                ],
            ),
            started_at=started_at,
            completed_at=completed_at,
        )

        self._session.add(execution)

        try:
            self._session.flush()

        except IntegrityError as exc:
            raise DuplicateRecordError(
                "Agent sequence "
                f"{sequence_number} already exists "
                "for this analysis."
            ) from exc

        return execution

    def list_for_analysis(
        self,
        analysis_id: str,
    ) -> list[AgentExecutionRecord]:
        """Return ordered executions for one analysis."""

        statement = (
            select(AgentExecutionRecord)
            .where(
                AgentExecutionRecord.analysis_id
                == analysis_id
            )
            .order_by(
                AgentExecutionRecord
                .sequence_number
                .asc()
            )
        )

        return list(
            self._session.scalars(
                statement
            )
        )

    @classmethod
    def _extract_usage(
        cls,
        output_payload: dict[str, Any] | None,
    ) -> dict[str, int | None]:
        """Extract provider usage metadata from an AI output."""

        empty_usage = {
            "prompt_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "thought_tokens": None,
        }

        if output_payload is None:
            return empty_usage

        metadata = output_payload.get(
            "_ai_metadata"
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            return empty_usage

        usage = metadata.get(
            "usage"
        )

        if not isinstance(
            usage,
            Mapping,
        ):
            return empty_usage

        return {
            "prompt_tokens": (
                cls._read_token_value(
                    usage.get("prompt_tokens")
                )
            ),
            "output_tokens": (
                cls._read_token_value(
                    usage.get("output_tokens")
                )
            ),
            "total_tokens": (
                cls._read_token_value(
                    usage.get("total_tokens")
                )
            ),
            "thought_tokens": (
                cls._read_token_value(
                    usage.get("thought_tokens")
                )
            ),
        }

    @classmethod
    def _resolve_token_value(
        cls,
        *,
        explicit_value: int | None,
        extracted_value: int | None,
    ) -> int | None:
        """Prefer an explicit token value over extracted metadata."""

        if explicit_value is not None:
            validated_value = cls._read_token_value(
                explicit_value
            )

            if validated_value is None:
                raise ValueError(
                    "Token values must be non-negative integers."
                )

            return validated_value

        return extracted_value

    @staticmethod
    def _read_token_value(
        value: Any,
    ) -> int | None:
        """Read one optional non-negative token count."""

        if isinstance(value, bool):
            return None

        if (
            isinstance(value, int)
            and value >= 0
        ):
            return value

        return None

    @staticmethod
    def _normalize_required_text(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """Normalize required repository text."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalized_value