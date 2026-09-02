"""Schemas shared across CFO.ai workflows."""

from pydantic import Field

from src.schemas.common import StrictModel
from src.schemas.controller import ControllerResult
from src.schemas.general_ledger import GeneralLedgerResult


class WorkflowResultBase(StrictModel):
    """Base fields shared by all workflow outputs."""

    correlation_id: str = Field(min_length=1)
    final_status: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class GLControllerWorkflowResult(WorkflowResultBase):
    """Combined result of the GL to Controller workflow."""

    general_ledger_result: GeneralLedgerResult
    controller_result: ControllerResult