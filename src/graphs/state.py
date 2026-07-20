"""Shared LangGraph state for the CFO.ai finance graph."""

from typing import Any, TypedDict

from src.schemas.controller import ControllerResult
from src.schemas.general_ledger import (
    GeneralLedgerResult,
    LedgerTransactionInput,
)


class CFOGraphState(TypedDict, total=False):
    correlation_id: str

    input_data: LedgerTransactionInput
    metadata: dict[str, Any]

    general_ledger_result: GeneralLedgerResult
    controller_result: ControllerResult

    current_step: str
    completed_steps: list[str]

    final_status: str
    summary: str

    errors: list[str]