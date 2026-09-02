from src.orchestrator.registry import AgentRegistry


def test_register_and_get_agent():
    registry = AgentRegistry()

    agent = object()

    registry.register("general_ledger", agent)

    assert registry.get("general_ledger") is agent


def test_contains_registered_agent():
    registry = AgentRegistry()

    registry.register("controller", object())

    assert registry.contains("controller")


def test_list_registered_agents():
    registry = AgentRegistry()

    registry.register("controller", object())
    registry.register("general_ledger", object())

    assert registry.list_agents() == [
        "controller",
        "general_ledger",
    ]


def test_duplicate_registration_raises_error():
    registry = AgentRegistry()

    registry.register("controller", object())

    try:
        registry.register("controller", object())
        assert False
    except ValueError:
        pass


def test_unregister_agent():
    registry = AgentRegistry()

    registry.register("controller", object())

    registry.unregister("controller")

    assert not registry.contains("controller")



def test_get_definition_returns_agent_metadata():
    registry = AgentRegistry()
    agent = object()

    registry.register(
        " General_Ledger ",
        agent,
        description=" Handles Journal Entries ",
        required_inputs={" Request ", "Context"},
        capabilities={" Create Entry ", "Validate Entry"},
    )

    definition = registry.get_definition("general_ledger")

    assert definition.name == "general_ledger"
    assert definition.agent is agent
    assert definition.description == "Handles Journal Entries"
    assert definition.required_inputs == frozenset(
        {"request", "context"}
    )
    assert definition.capabilities == frozenset(
        {"create entry", "validate entry"}
    )


def test_get_still_returns_agent_object():
    registry = AgentRegistry()
    agent = object()

    registry.register(
        "general_ledger",
        agent,
        description="Handles journal entries",
    )

    assert registry.get("general_ledger") is agent


def test_definition_metadata_is_immutable():
    registry = AgentRegistry()

    registry.register(
        "general_ledger",
        object(),
        required_inputs={"request"},
    )

    definition = registry.get_definition("general_ledger")

    try:
        definition.name = "controller"
        assert False
    except (AttributeError, TypeError):
        pass


def test_invalid_metadata_value_is_rejected():
    registry = AgentRegistry()

    try:
        registry.register(
            "general_ledger",
            object(),
            required_inputs={"request", ""},
        )
        assert False
    except ValueError:
        pass