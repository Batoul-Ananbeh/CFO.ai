"""Agent registry for the CFO.ai orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Describe an agent and the contract required to execute it."""

    name: str
    agent: Any
    description: str = ""
    required_inputs: frozenset[str] = field(default_factory=frozenset)
    capabilities: frozenset[str] = field(default_factory=frozenset)


class AgentRegistry:
    """Store and retrieve agent definitions by unique names."""

    def __init__(self) -> None:
        self._definitions: dict[str, AgentDefinition] = {}

    def register(
        self,
        name: str,
        agent: Any,
        *,
        description: str = "",
        required_inputs: set[str] | frozenset[str] | None = None,
        capabilities: set[str] | frozenset[str] | None = None,
    ) -> None:
        """Register an agent and its execution metadata."""
        normalized_name = self._normalize_name(name)

        if normalized_name in self._definitions:
            raise ValueError(
                f"Agent '{normalized_name}' is already registered."
            )

        definition = AgentDefinition(
            name=normalized_name,
            agent=agent,
            description=description.strip(),
            required_inputs=self._normalize_values(required_inputs),
            capabilities=self._normalize_values(capabilities),
        )

        self._definitions[normalized_name] = definition

    def get(self, name: str) -> Any:
        """Return the registered agent object.

        This preserves compatibility with the existing registry interface.
        """
        return self.get_definition(name).agent

    def get_definition(self, name: str) -> AgentDefinition:
        """Return the complete definition of a registered agent."""
        normalized_name = self._normalize_name(name)

        if normalized_name not in self._definitions:
            raise KeyError(
                f"Agent '{normalized_name}' is not registered."
            )

        return self._definitions[normalized_name]

    def contains(self, name: str) -> bool:
        normalized_name = self._normalize_name(name)
        return normalized_name in self._definitions

    def list_agents(self) -> list[str]:
        return sorted(self._definitions.keys())

    def unregister(self, name: str) -> None:
        normalized_name = self._normalize_name(name)

        if normalized_name not in self._definitions:
            raise KeyError(
                f"Agent '{normalized_name}' is not registered."
            )

        del self._definitions[normalized_name]

    @staticmethod
    def _normalize_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Agent name must be a string.")

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("Agent name cannot be empty.")

        return normalized_name

    @staticmethod
    def _normalize_values(
        values: set[str] | frozenset[str] | None,
    ) -> frozenset[str]:
        if values is None:
            return frozenset()

        normalized_values: set[str] = set()

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    "Agent metadata values must be strings."
                )

            normalized_value = value.strip().lower()

            if not normalized_value:
                raise ValueError(
                    "Agent metadata values cannot be empty."
                )

            normalized_values.add(normalized_value)

        return frozenset(normalized_values)