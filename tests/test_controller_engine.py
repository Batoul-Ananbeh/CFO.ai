"""Manual tests for the Controller validation engine."""

from decimal import Decimal

from src.engines.controller_validation_engine import validate_trial_balance
from src.schemas.common import Money
from src.schemas.controller import TrialBalanceInput


def test_unbalanced_trial_balance() -> None:
    input_data = TrialBalanceInput(
        report_id="TB-001",
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

    result = validate_trial_balance(
        input_data=input_data,
        correlation_id="CORR-001",
    )

    print("\n=== UNBALANCED TRIAL BALANCE ===")
    print(result.model_dump_json(indent=2))

    assert result.decision_status == "REQUIRES_CORRECTION"
    assert result.balance_difference is not None
    assert result.balance_difference.amount == Decimal("1250")
    assert result.severity == "HIGH"


def test_balanced_trial_balance() -> None:
    input_data = TrialBalanceInput(
        report_id="TB-002",
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

    result = validate_trial_balance(
        input_data=input_data,
        correlation_id="CORR-002",
    )

    print("\n=== BALANCED TRIAL BALANCE ===")
    print(result.model_dump_json(indent=2))

    assert result.decision_status == "APPROVED"
    assert result.balance_difference is not None
    assert result.balance_difference.amount == Decimal("0")
    assert result.severity == "INFO"


if __name__ == "__main__":
    test_unbalanced_trial_balance()
    test_balanced_trial_balance()

    print("\nAll Controller Engine tests passed successfully.")