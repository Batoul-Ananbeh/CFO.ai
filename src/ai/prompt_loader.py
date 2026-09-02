"""Utilities for loading CFO.ai prompt files."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path


PROMPTS_DIRECTORY = Path(__file__).resolve().parent / "prompts"

_VALID_PROMPT_NAME = re.compile(r"^[a-z0-9_]+$")


def _validate_prompt_name(prompt_name: str) -> str:
    """
    Validate a prompt name before using it as a file name.

    This prevents unsupported names and path traversal attempts.
    """

    normalized_name = prompt_name.strip().lower()

    if not normalized_name:
        raise ValueError("Prompt name cannot be empty.")

    if not _VALID_PROMPT_NAME.fullmatch(normalized_name):
        raise ValueError(
            "Prompt name may contain only lowercase letters, "
            "numbers, and underscores."
        )

    return normalized_name


@lru_cache(maxsize=64)
def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt from src/ai/prompts.

    Example:
        load_prompt("general_ledger")
    """

    normalized_name = _validate_prompt_name(prompt_name)

    prompt_path = PROMPTS_DIRECTORY / f"{normalized_name}.md"

    if not prompt_path.is_file():
        raise FileNotFoundError(
            f"Prompt file was not found: {prompt_path}"
        )

    prompt_content = prompt_path.read_text(encoding="utf-8").strip()

    if not prompt_content:
        raise ValueError(
            f"Prompt file is empty: {prompt_path}"
        )

    return prompt_content


@lru_cache(maxsize=64)
def load_agent_prompt(agent_prompt_name: str) -> str:
    """
    Combine the global base prompt with an agent-specific prompt.
    """

    base_prompt = load_prompt("base")
    agent_prompt = load_prompt(agent_prompt_name)

    return (
        f"{base_prompt}\n\n"
        f"AGENT-SPECIFIC RESPONSIBILITIES:\n\n"
        f"{agent_prompt}"
    )


def clear_prompt_cache() -> None:
    """Clear prompt caches, mainly for testing and development."""

    load_prompt.cache_clear()
    load_agent_prompt.cache_clear()