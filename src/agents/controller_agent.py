"""Financial Controller Agent implementation."""

from __future__ import annotations
from src.agents.controller_explanation import explain_controller_result
from src.engines.controller_validation_engine import (
    validate_journal_entry_balance,
    validate_trial_balance,
)
from src.schemas.controller import ControllerResult, TrialBalanceInput
from src.schemas.enums import ReportType


class FinancialControllerAgent:
    """
    Validate financial reports using deterministic financial engines.

    The Agent coordinates validation but does not perform hidden financial
    calculations or execute financial transactions.
    """

    agent_name = "financial_controller_agent"

    def explain(
        self,
        result: ControllerResult,
    ) -> str:
        """Explain a validated result without changing its decision."""

        return explain_controller_result(result)
    
    def review_trial_balance(
        self,
        input_data: TrialBalanceInput,
        correlation_id: str,
    ) -> ControllerResult:
        """Validate a trial balance and return a structured result."""

        return validate_trial_balance(
            input_data=input_data,
            correlation_id=correlation_id,
        )

    def review(
        self,
        report_type: ReportType,
        input_data: TrialBalanceInput,
        correlation_id: str,
    ) -> ControllerResult:
        """
        Route a supported report to the correct validation engine.

        Additional report types will be added later.
        """

        if report_type == ReportType.TRIAL_BALANCE:
            return self.review_trial_balance(
                input_data=input_data,
                correlation_id=correlation_id,
            )

        if report_type == ReportType.JOURNAL_ENTRY:
            return validate_journal_entry_balance(
                input_data=input_data,
                correlation_id=correlation_id,
            )

        raise NotImplementedError(
            f"Controller review for {report_type.value} "
            "is not implemented yet."
        )
