"""Dispatcher for executing orchestrator plans."""

from __future__ import annotations

from src.orchestrator.context import ExecutionContext
from src.orchestrator.errors import ExecutionError
from src.orchestrator.registry import AgentRegistry


class Dispatcher:
    """Execute agents selected by the planner."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def dispatch(
        self,
        plan: list[str],
        context: ExecutionContext,
        *,
        fail_fast: bool = False,
    ) -> ExecutionContext:
        """Execute all agents in the supplied plan."""

        if not plan:
            raise ValueError("Execution plan cannot be empty.")

        for agent_name in plan:
            definition = self._registry.get_definition(agent_name)

            try:
                self._validate_required_inputs(
                    agent_name=definition.name,
                    required_inputs=definition.required_inputs,
                    context=context,
                )

                agent = definition.agent

                if not hasattr(agent, "execute"):
                    raise AttributeError(
                        f"Agent '{definition.name}' "
                        "does not implement execute()."
                    )

                result = agent.execute(context=context)

                context.set_result(
                    definition.name,
                    result,
                )

            except Exception as exception:
                execution_error = ExecutionError.from_exception(
                    agent_name=definition.name,
                    exception=exception,
                )

                context.add_error(execution_error)

                if fail_fast:
                    raise

        return context

    @staticmethod
    def _validate_required_inputs(
        *,
        agent_name: str,
        required_inputs: frozenset[str],
        context: ExecutionContext,
    ) -> None:
        """Ensure the execution context contains required inputs."""

        missing_inputs = [
            input_name
            for input_name in sorted(required_inputs)
            if not Dispatcher._context_has_value(
                context=context,
                input_name=input_name,
            )
        ]

        if missing_inputs:
            missing_text = ", ".join(missing_inputs)

            raise ValueError(
                f"Agent '{agent_name}' is missing required inputs: "
                f"{missing_text}."
            )

    @staticmethod
    def _context_has_value(
        *,
        context: ExecutionContext,
        input_name: str,
    ) -> bool:
        """Check context fields, metadata and previous results."""

        if hasattr(context, input_name):
            value = getattr(context, input_name)

            if value is not None and value != "":
                return True

        if input_name in context.metadata:
            value = context.metadata[input_name]

            if value is not None and value != "":
                return True

        if context.has_result(input_name):
            value = context.get_result(input_name)

            if value is not None:
                return True

        return False