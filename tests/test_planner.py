from src.orchestrator.planner import Planner


def test_plan_general_ledger():
    planner = Planner()

    result = planner.plan(
        "Create a journal entry"
    )

    assert result == ["general_ledger"]


def test_plan_controller():
    planner = Planner()

    result = planner.plan(
        "Review the trial balance"
    )

    assert result == ["controller"]


def test_empty_request():
    planner = Planner()

    try:
        planner.plan("")
        assert False
    except ValueError:
        pass


def test_unknown_request():
    planner = Planner()

    try:
        planner.plan(
            "Prepare coffee"
        )
        assert False
    except ValueError:
        pass