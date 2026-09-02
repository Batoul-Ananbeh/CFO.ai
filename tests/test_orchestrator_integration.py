from src.orchestrator.dispatcher import Dispatcher
from src.orchestrator.orchestrator import Orchestrator
from src.orchestrator.planner import Planner
from src.orchestrator.registry import AgentRegistry


class FakeGeneralLedgerAgent:
    def execute(self, context):
        return {
            "status": "success",
            "request": context.request,
        }


def test_orchestrator_runs_general_ledger_request():
    registry = AgentRegistry()

    registry.register(
        name="general_ledger",
        agent=FakeGeneralLedgerAgent(),
    )

    planner = Planner()

    dispatcher = Dispatcher(registry)

    orchestrator = Orchestrator(
        planner=planner,
        dispatcher=dispatcher,
    )

    context = orchestrator.run(
        "Create journal entry for cash sale"
    )

    assert context.errors == []

    assert context.has_result("general_ledger")

    result = context.get_result("general_ledger")

    assert result["status"] == "success"

    assert (
        result["request"]
        == "Create journal entry for cash sale"
    )


class SequentialPlanner:
    def plan(self, request: str) -> list[str]:
        return [
            "general_ledger",
            "controller",
        ]


class SequentialGeneralLedgerAgent:
    def execute(self, context):
        execution_order = context.metadata.setdefault(
            "execution_order",
            [],
        )
        execution_order.append("general_ledger")

        return {
            "status": "ready_for_controller_review",
            "total_debit": 1000,
            "total_credit": 1000,
        }


class SequentialControllerAgent:
    def execute(self, context):
        execution_order = context.metadata.setdefault(
            "execution_order",
            [],
        )
        execution_order.append("controller")

        ledger_result = context.get_result("general_ledger")

        return {
            "status": "approved",
            "ledger_status": ledger_result["status"],
            "balanced": (
                ledger_result["total_debit"]
                == ledger_result["total_credit"]
            ),
        }


def test_orchestrator_runs_multiple_agents_in_sequence():
    registry = AgentRegistry()

    registry.register(
        name="general_ledger",
        agent=SequentialGeneralLedgerAgent(),
    )

    registry.register(
        name="controller",
        agent=SequentialControllerAgent(),
        required_inputs={"general_ledger"},
    )

    dispatcher = Dispatcher(registry)

    orchestrator = Orchestrator(
        planner=SequentialPlanner(),
        dispatcher=dispatcher,
    )

    context = orchestrator.run(
        "Create and review a balanced journal entry"
    )

    assert context.errors == []

    assert context.metadata["execution_order"] == [
        "general_ledger",
        "controller",
    ]

    assert context.has_result("general_ledger")
    assert context.has_result("controller")

    ledger_result = context.get_result("general_ledger")
    controller_result = context.get_result("controller")

    assert (
        ledger_result["status"]
        == "ready_for_controller_review"
    )

    assert controller_result["status"] == "approved"
    assert controller_result["balanced"] is True

    assert (
        controller_result["ledger_status"]
        == "ready_for_controller_review"
    )


class DataFlowPlanner:
    def plan(self, request: str) -> list[str]:
        return [
            "general_ledger",
            "controller",
        ]


class DataFlowGeneralLedgerAgent:
    def execute(self, context):
        return {
            "journal_id": "JRN-2026-001",
            "accounting_period": "2026-07",
            "currency": "USD",
            "total_debit": 1500,
            "total_credit": 1500,
            "entries": [
                {
                    "account_code": "1100",
                    "account_name": "Bank",
                    "debit": 1500,
                    "credit": 0,
                },
                {
                    "account_code": "4100",
                    "account_name": "Sales Revenue",
                    "debit": 0,
                    "credit": 1500,
                },
            ],
        }


class DataFlowControllerAgent:
    def execute(self, context):
        ledger_result = context.get_result("general_ledger")

        return {
            "received_journal_id": ledger_result["journal_id"],
            "received_accounting_period": (
                ledger_result["accounting_period"]
            ),
            "received_currency": ledger_result["currency"],
            "received_total_debit": ledger_result["total_debit"],
            "received_total_credit": ledger_result["total_credit"],
            "received_entries": ledger_result["entries"],
            "balanced": (
                ledger_result["total_debit"]
                == ledger_result["total_credit"]
            ),
        }


def test_orchestrator_preserves_data_between_agents():
    registry = AgentRegistry()

    registry.register(
        name="general_ledger",
        agent=DataFlowGeneralLedgerAgent(),
    )

    registry.register(
        name="controller",
        agent=DataFlowControllerAgent(),
        required_inputs={"general_ledger"},
    )

    orchestrator = Orchestrator(
        planner=DataFlowPlanner(),
        dispatcher=Dispatcher(registry),
    )

    context = orchestrator.run(
        "Create and validate a journal entry"
    )

    assert context.errors == []

    ledger_result = context.get_result("general_ledger")
    controller_result = context.get_result("controller")

    assert (
        controller_result["received_journal_id"]
        == ledger_result["journal_id"]
    )

    assert (
        controller_result["received_accounting_period"]
        == ledger_result["accounting_period"]
    )

    assert (
        controller_result["received_currency"]
        == ledger_result["currency"]
    )

    assert (
        controller_result["received_total_debit"]
        == ledger_result["total_debit"]
    )

    assert (
        controller_result["received_total_credit"]
        == ledger_result["total_credit"]
    )

    assert (
        controller_result["received_entries"]
        == ledger_result["entries"]
    )

    assert controller_result["balanced"] is True


class FaultTolerancePlanner:
    def plan(self, request: str) -> list[str]:
        return [
            "general_ledger",
            "controller",
            "treasury",
            "fpa",
        ]


class SuccessfulLedgerAgent:
    def execute(self, context):
        return {
            "status": "ready_for_review",
            "cash_balance": 5000,
        }


class FailingControllerAgent:
    def execute(self, context):
        raise RuntimeError("Controller service unavailable.")


class SuccessfulTreasuryAgent:
    def execute(self, context):
        ledger_result = context.get_result("general_ledger")

        return {
            "status": "completed",
            "available_cash": ledger_result["cash_balance"],
        }


class SuccessfulFPAAgent:
    def execute(self, context):
        treasury_result = context.get_result("treasury")

        return {
            "status": "forecast_completed",
            "forecast_base": treasury_result["available_cash"],
        }


def test_orchestrator_continues_after_agent_failure():
    registry = AgentRegistry()

    registry.register(
        name="general_ledger",
        agent=SuccessfulLedgerAgent(),
    )

    registry.register(
        name="controller",
        agent=FailingControllerAgent(),
        required_inputs={"general_ledger"},
    )

    registry.register(
        name="treasury",
        agent=SuccessfulTreasuryAgent(),
        required_inputs={"general_ledger"},
    )

    registry.register(
        name="fpa",
        agent=SuccessfulFPAAgent(),
        required_inputs={"treasury"},
    )

    orchestrator = Orchestrator(
        planner=FaultTolerancePlanner(),
        dispatcher=Dispatcher(registry),
    )

    context = orchestrator.run(
        "Process finance workflow with fault tolerance"
    )

    assert context.has_result("general_ledger")
    assert not context.has_result("controller")
    assert context.has_result("treasury")
    assert context.has_result("fpa")

    assert len(context.errors) == 1

    error = context.errors[0]

    assert error.agent_name == "controller"
    assert error.exception_type == "RuntimeError"
    assert error.message == "Controller service unavailable."

    treasury_result = context.get_result("treasury")
    fpa_result = context.get_result("fpa")

    assert treasury_result["status"] == "completed"
    assert treasury_result["available_cash"] == 5000

    assert fpa_result["status"] == "forecast_completed"
    assert fpa_result["forecast_base"] == 5000