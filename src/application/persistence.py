"""Application persistence service for CFO.ai analyses."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from src.ai.context_utils import (
    to_json_compatible,
)
from src.application.models import (
    CFOAnalysisRequest,
    CFOAnalysisResponse,
    CFOExecutionError,
)
from src.database.models import (
    Branch,
    Company,
)
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)


UnitOfWorkFactory = Callable[
    [],
    PersistenceUnitOfWork,
]


class AnalysisPersistenceService:
    """Persist complete CFO analyses and execution histories."""

    def __init__(
        self,
        *,
        unit_of_work_factory: (
            UnitOfWorkFactory | None
        ) = None,
    ) -> None:
        self._unit_of_work_factory = (
            unit_of_work_factory
            if unit_of_work_factory is not None
            else PersistenceUnitOfWork
        )

    def persist(
        self,
        *,
        analysis_request: CFOAnalysisRequest,
        response: CFOAnalysisResponse,
        started_at: Any = None,
        completed_at: Any = None,
    ) -> str:
        """Persist one analysis and return its database ID."""

        if not response.correlation_id:
            raise ValueError(
                "A correlation ID is required before persistence."
            )

        financial_input = self._json_dict(
            analysis_request.financial_input,
            field_name="Financial input",
        )

        metadata = self._json_dict(
            analysis_request.metadata,
            field_name="Metadata",
        )

        verified_results = self._json_dict(
            response.verified_results,
            field_name="Verified results",
        )

        ai_results = self._json_dict(
            response.ai_results,
            field_name="AI results",
        )

        errors = [
            error.model_dump(
                mode="json"
            )
            for error in response.errors
        ]

        with self._unit_of_work_factory() as unit_of_work:
            company = self._resolve_company(
                unit_of_work=unit_of_work,
                metadata=metadata,
                financial_input=financial_input,
            )

            branch = self._resolve_branch(
                unit_of_work=unit_of_work,
                company=company,
                metadata=metadata,
            )

            analysis = unit_of_work.analyses.create(
                company_id=company.id,
                branch_id=(
                    branch.id
                    if branch is not None
                    else None
                ),
                correlation_id=(
                    response.correlation_id
                ),
                request_text=response.request,
                status=response.status.value,
                financial_input=financial_input,
                metadata_payload=metadata,
                execution_plan=list(
                    response.execution_plan
                ),
                executed_agents=list(
                    response.executed_agents
                ),
                verified_results=verified_results,
                ai_results=ai_results,
                final_agent=response.final_agent,
                final_output=(
                    self._json_optional_dict(
                        response.final_output
                    )
                ),
                errors=errors,
                started_at=started_at,
                completed_at=completed_at,
            )

            self._persist_agent_executions(
                unit_of_work=unit_of_work,
                analysis_id=analysis.id,
                request=response.request,
                financial_input=financial_input,
                response=response,
            )

            unit_of_work.audit_logs.create(
                company_id=company.id,
                branch_id=(
                    branch.id
                    if branch is not None
                    else None
                ),
                analysis_id=analysis.id,
                action=(
                    f"ANALYSIS_{response.status.value}"
                ),
                entity_type="analysis",
                entity_id=analysis.id,
                details={
                    "correlation_id": (
                        response.correlation_id
                    ),
                    "status": response.status.value,
                    "execution_plan": list(
                        response.execution_plan
                    ),
                    "executed_agents": list(
                        response.executed_agents
                    ),
                    "final_agent": (
                        response.final_agent
                    ),
                    "error_count": len(
                        response.errors
                    ),
                },
            )

            return analysis.id

    def _persist_agent_executions(
        self,
        *,
        unit_of_work: PersistenceUnitOfWork,
        analysis_id: str,
        request: str,
        financial_input: dict[str, Any],
        response: CFOAnalysisResponse,
    ) -> None:
        """Persist deterministic and AI execution records."""

        errors_by_agent = {
            error.agent_name: error
            for error in response.errors
        }

        deterministic_error = errors_by_agent.get(
            "deterministic_finance"
        )

        unit_of_work.agent_executions.create(
            analysis_id=analysis_id,
            agent_name="deterministic_finance",
            sequence_number=1,
            status=(
                "FAILED"
                if deterministic_error is not None
                else "COMPLETED"
            ),
            input_payload=financial_input,
            output_payload=(
                response.verified_results
                if deterministic_error is None
                else None
            ),
            error_category=(
                deterministic_error.category.value
                if deterministic_error is not None
                else None
            ),
            error_message=(
                deterministic_error.message
                if deterministic_error is not None
                else None
            ),
            provider_status_code=(
                deterministic_error.provider_status_code
                if deterministic_error is not None
                else None
            ),
            retryable=(
                deterministic_error.retryable
                if deterministic_error is not None
                else False
            ),
        )

        executed_agent_names = set(
            response.executed_agents
        )

        for sequence_number, agent_name in enumerate(
            response.execution_plan,
            start=2,
        ):
            error = errors_by_agent.get(
                agent_name
            )

            if agent_name in executed_agent_names:
                execution_status = "COMPLETED"

            elif error is not None:
                execution_status = "FAILED"

            else:
                execution_status = "SKIPPED"

            raw_output = response.ai_results.get(
                agent_name
            )

            output_payload = (
                self._json_optional_dict(
                    raw_output
                )
            )

            unit_of_work.agent_executions.create(
                analysis_id=analysis_id,
                agent_name=agent_name,
                sequence_number=sequence_number,
                status=execution_status,
                input_payload={
                    "request": request,
                    "verified_result_keys": sorted(
                        response.verified_results.keys()
                    ),
                },
                output_payload=output_payload,
                error_category=(
                    error.category.value
                    if error is not None
                    else None
                ),
                error_message=(
                    error.message
                    if error is not None
                    else None
                ),
                provider_status_code=(
                    error.provider_status_code
                    if error is not None
                    else None
                ),
                retryable=(
                    error.retryable
                    if error is not None
                    else False
                ),
            )

    def _resolve_company(
        self,
        *,
        unit_of_work: PersistenceUnitOfWork,
        metadata: Mapping[str, Any],
        financial_input: Mapping[str, Any],
    ) -> Company:
        """Resolve or automatically create the request company."""

        raw_company_reference = (
            metadata.get("company_id")
            or metadata.get("company_code")
            or "DEFAULT-COMPANY"
        )

        company_reference = self._required_text(
            raw_company_reference,
            field_name="Company reference",
        )

        company = unit_of_work.companies.get_by_id(
            company_reference
        )

        if company is None:
            company = (
                unit_of_work.companies.get_by_code(
                    company_reference
                )
            )

        if company is not None:
            return company

        company_name = self._optional_text(
            metadata.get("company_name")
        )

        if company_name is None:
            company_name = (
                company_reference
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )

        base_currency = self._resolve_currency(
            metadata=metadata,
            financial_input=financial_input,
        )

        return unit_of_work.companies.create(
            code=company_reference,
            name=company_name,
            base_currency=base_currency,
        )

    def _resolve_branch(
        self,
        *,
        unit_of_work: PersistenceUnitOfWork,
        company: Company,
        metadata: Mapping[str, Any],
    ) -> Branch | None:
        """Resolve or automatically create an optional branch."""

        raw_branch_reference = (
            metadata.get("branch_id")
            or metadata.get("branch_code")
        )

        if raw_branch_reference is None:
            return None

        branch_reference = self._required_text(
            raw_branch_reference,
            field_name="Branch reference",
        )

        branch = unit_of_work.branches.get_by_id(
            branch_reference
        )

        if (
            branch is not None
            and branch.company_id == company.id
        ):
            return branch

        branch = (
            unit_of_work.branches
            .get_by_company_and_code(
                company_id=company.id,
                code=branch_reference,
            )
        )

        if branch is not None:
            return branch

        branch_name = self._optional_text(
            metadata.get("branch_name")
        )

        if branch_name is None:
            branch_name = (
                branch_reference
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )

        return unit_of_work.branches.create(
            company_id=company.id,
            code=branch_reference,
            name=branch_name,
            external_reference=(
                self._optional_text(
                    metadata.get(
                        "branch_external_reference"
                    )
                )
            ),
        )

    @staticmethod
    def _resolve_currency(
        *,
        metadata: Mapping[str, Any],
        financial_input: Mapping[str, Any],
    ) -> str:
        """Resolve the company base currency."""

        metadata_currency = metadata.get(
            "base_currency"
        )

        if isinstance(
            metadata_currency,
            str,
        ) and metadata_currency.strip():
            return metadata_currency.strip().upper()

        amount_payload = financial_input.get(
            "amount"
        )

        if isinstance(
            amount_payload,
            Mapping,
        ):
            input_currency = amount_payload.get(
                "currency"
            )

            if isinstance(
                input_currency,
                str,
            ) and input_currency.strip():
                return input_currency.strip().upper()

        return "JOD"

    @staticmethod
    def _json_dict(
        value: Any,
        *,
        field_name: str,
    ) -> dict[str, Any]:
        """Convert a value into a JSON-compatible dictionary."""

        converted_value = to_json_compatible(
            value
        )

        if not isinstance(
            converted_value,
            dict,
        ):
            raise TypeError(
                f"{field_name} must serialize to a dictionary."
            )

        return converted_value

    @staticmethod
    def _json_optional_dict(
        value: Any,
    ) -> dict[str, Any] | None:
        """Convert an optional output to a JSON dictionary."""

        if value is None:
            return None

        converted_value = to_json_compatible(
            value
        )

        if isinstance(
            converted_value,
            dict,
        ):
            return converted_value

        return {
            "result": converted_value,
        }

    @staticmethod
    def _required_text(
        value: Any,
        *,
        field_name: str,
    ) -> str:
        """Normalize required text metadata."""

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

    @staticmethod
    def _optional_text(
        value: Any,
    ) -> str | None:
        """Normalize optional text metadata."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "Optional metadata text must be a string."
            )

        normalized_value = value.strip()

        return (
            normalized_value
            if normalized_value
            else None
        )