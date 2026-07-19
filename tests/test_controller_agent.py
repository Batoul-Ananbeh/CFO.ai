"""Tests for the Financial Controller Agent."""

from decimal import Decimal

import pytest

from src.agents.controller_agent import FinancialControllerAgent
from src.schemas.common import Money
from src.schemas.controller import TrialBalanceInput
from src.schemas.enums import (
    ControllerDecisionStatus,
    ReportType,
    Severity,
)


def test_controller_agent_approves_balanced_trial_balance() -> None:
    agent = FinancialControllerAgent()

    input_data = TrialBalanceInput(
        report_id="TB-AGENT-001",
        accounting_period="2026-07",
        total_debit=Money(
            amount=Decimal("15000"),
            currency="USD",
        ),
        total_credit=Money(
            amount=Decimal("15000"),
            currency="USD",
        ),
    )

    result = agent.review(
        report_type=ReportType.TRIAL_BALANCE,
        input_data=input_data,
        correlation_id="CORR-AGENT-001",
    )

    assert result.decision_status == ControllerDecisionStatus.APPROVED
    assert result.severity == Severity.INFO
    assert result.balance_difference is not None
    assert result.balance_difference.amount == Decimal("0")


def test_controller_agent_rejects_unbalanced_trial_balance() -> None:
    agent = FinancialControllerAgent()

    input_data = TrialBalanceInput(
        report_id="TB-AGENT-002",
        accounting_period="2026-07",
        total_debit=Money(
            amount=Decimal("15000"),
            currency="JOD",
        ),
        total_credit=Money(
            amount=Decimal("13750"),
            currency="JOD",
        ),
    )

    result = agent.review(
        report_type=ReportType.TRIAL_BALANCE,
        input_data=input_data,
        correlation_id="CORR-AGENT-002",
    )

    assert (
        result.decision_status
        == ControllerDecisionStatus.REQUIRES_CORRECTION
    )
    assert result.severity == Severity.HIGH
    assert result.balance_difference is not None
    assert result.balance_difference.amount == Decimal("1250")
    assert len(result.issues) == 1
    assert len(result.required_actions) == 1


def test_controller_agent_rejects_unsupported_report_type() -> None:
    agent = FinancialControllerAgent()

    input_data = TrialBalanceInput(
        report_id="TB-AGENT-003",
        accounting_period="2026-07",
        total_debit=Money(
            amount=Decimal("100"),
            currency="EUR",
        ),
        total_credit=Money(
            amount=Decimal("100"),
            currency="EUR",
        ),
    )

    with pytest.raises(NotImplementedError):
        agent.review(
            report_type=ReportType.PAYROLL,
            input_data=input_data,
            correlation_id="CORR-AGENT-003",
        )


def test_controller_agent_explains_unbalanced_result() -> None:
    agent = FinancialControllerAgent()

    input_data = TrialBalanceInput(
        report_id="TB-EXPLAIN-001",
        accounting_period="2026-07",
        total_debit=Money(
            amount=Decimal("15000"),
            currency="JOD",
        ),
        total_credit=Money(
            amount=Decimal("13750"),
            currency="JOD",
        ),
    )

    result = agent.review(
        report_type=ReportType.TRIAL_BALANCE,
        input_data=input_data,
        correlation_id="CORR-EXPLAIN-001",
    )

    explanation = agent.explain(result)

    assert "1250" in explanation
    assert "JOD" in explanation
    assert "لا يمكن اعتماد" in explanation


def test_controller_agent_explains_approved_result() -> None:
    agent = FinancialControllerAgent()

    input_data = TrialBalanceInput(
        report_id="TB-EXPLAIN-002",
        accounting_period="2026-07",
        total_debit=Money(
            amount=Decimal("5000"),
            currency="EUR",
        ),
        total_credit=Money(
            amount=Decimal("5000"),
            currency="EUR",
        ),
    )

    result = agent.review(
        report_type=ReportType.TRIAL_BALANCE,
        input_data=input_data,
        correlation_id="CORR-EXPLAIN-002",
    )

    explanation = agent.explain(result)

    assert "تم اعتماد" in explanation
    assert "لا يوجد فرق" in explanation