"""Inspect the latest CFO.ai analysis stored in PostgreSQL."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.models import (
    AnalysisRecord,
    AuditLogRecord,
)
from src.database.session import (
    get_session_factory,
)


def to_printable_json(
    value: Any,
) -> str:
    """Convert a value into readable JSON text."""

    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def main() -> None:
    """Print the latest persisted analysis and execution history."""

    session_factory = get_session_factory()

    with session_factory() as session:
        statement = (
            select(AnalysisRecord)
            .options(
                selectinload(
                    AnalysisRecord.company
                ),
                selectinload(
                    AnalysisRecord.branch
                ),
                selectinload(
                    AnalysisRecord.agent_executions
                ),
            )
            .order_by(
                AnalysisRecord.created_at.desc()
            )
            .limit(1)
        )

        analysis = session.scalar(
            statement
        )

        if analysis is None:
            print(
                "No persisted analyses were found."
            )
            return

        audit_statement = (
            select(AuditLogRecord)
            .where(
                AuditLogRecord.analysis_id
                == analysis.id
            )
            .order_by(
                AuditLogRecord.created_at.asc()
            )
        )

        audit_logs = list(
            session.scalars(
                audit_statement
            )
        )

        company_name = (
            analysis.company.name
            if analysis.company is not None
            else None
        )

        company_code = (
            analysis.company.code
            if analysis.company is not None
            else None
        )

        branch_name = (
            analysis.branch.name
            if analysis.branch is not None
            else None
        )

        branch_code = (
            analysis.branch.code
            if analysis.branch is not None
            else None
        )

        print(
            "=== Latest CFO.ai Analysis ==="
        )

        print(
            f"Analysis ID: {analysis.id}"
        )

        print(
            "Correlation ID: "
            f"{analysis.correlation_id}"
        )

        print(
            f"Status: {analysis.status}"
        )

        print(
            f"Company: {company_name} "
            f"({company_code})"
        )

        print(
            f"Branch: {branch_name} "
            f"({branch_code})"
        )

        print(
            f"Request: {analysis.request_text}"
        )

        print(
            f"Final agent: {analysis.final_agent}"
        )

        print(
            "Created at: "
            f"{analysis.created_at}"
        )

        print(
            "Started at: "
            f"{analysis.started_at}"
        )

        print(
            "Completed at: "
            f"{analysis.completed_at}"
        )

        print()
        print("=== Execution Plan ===")

        for index, agent_name in enumerate(
            analysis.execution_plan,
            start=1,
        ):
            print(
                f"{index}. {agent_name}"
            )

        print()
        print("=== Agent Executions ===")

        for execution in (
            analysis.agent_executions
        ):
            print(
                f"{execution.sequence_number}. "
                f"{execution.agent_name}"
            )

            print(
                f"   Status: {execution.status}"
            )

            print(
                "   Error category: "
                f"{execution.error_category}"
            )

            print(
                "   Provider status: "
                f"{execution.provider_status_code}"
            )

            print(
                "   Retryable: "
                f"{execution.retryable}"
            )

            print(
                "   Total tokens: "
                f"{execution.total_tokens}"
            )

            if (
                execution.error_message
                is not None
            ):
                print(
                    "   Error message: "
                    f"{execution.error_message}"
                )

        print()
        print("=== Final Output ===")

        print(
            to_printable_json(
                analysis.final_output
            )
        )

        print()
        print("=== Errors ===")

        print(
            to_printable_json(
                analysis.errors
            )
        )

        print()
        print("=== Audit Logs ===")

        for audit_log in audit_logs:
            print(
                f"- {audit_log.action}"
            )

            print(
                "  Actor: "
                f"{audit_log.actor_type}"
            )

            print(
                "  Created at: "
                f"{audit_log.created_at}"
            )

            print(
                "  Details:"
            )

            print(
                to_printable_json(
                    audit_log.details
                )
            )


if __name__ == "__main__":
    main()