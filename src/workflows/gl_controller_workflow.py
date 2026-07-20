"""Workflow connecting the General Ledger Agent to the Controller Agent."""

from src.agents.controller_agent import FinancialControllerAgent
from src.agents.general_ledger_agent import GeneralLedgerAgent
from src.graphs.builder import build_gl_controller_graph
from src.schemas.general_ledger import LedgerTransactionInput
from src.schemas.workflows import GLControllerWorkflowResult
from src.workflows.base_workflow import BaseWorkflow


class GLControllerWorkflow(BaseWorkflow):
    """Run the GL-to-Controller process through LangGraph."""

    def __init__(
        self,
        gl_agent: GeneralLedgerAgent | None = None,
        controller_agent: FinancialControllerAgent | None = None,
    ) -> None:
        self.gl_agent = gl_agent or GeneralLedgerAgent()
        self.controller_agent = (
            controller_agent or FinancialControllerAgent()
        )

        self.graph = build_gl_controller_graph(
            gl_agent=self.gl_agent,
            controller_agent=self.controller_agent,
        )

    def run(
        self,
        input_data: LedgerTransactionInput,
        correlation_id: str,
    ) -> GLControllerWorkflowResult:
        correlation_id = self.validate_correlation_id(correlation_id)

        graph_result = self.graph.invoke(
            {
                "correlation_id": correlation_id,
                "input_data": input_data,
                "metadata": {
                    "workflow": "gl_controller",
                    "engine": "langgraph",
                },
                "current_step": "start",
                "completed_steps": [],
                "errors": [],
            }
        )

        general_ledger_result = self.require_result(
            graph_result.get("general_ledger_result"),
            "General Ledger Agent did not produce a result.",
        )

        controller_result = self.require_result(
            graph_result.get("controller_result"),
            "Controller Agent did not produce a result.",
        )

        final_status = self.require_result(
            graph_result.get("final_status"),
            "The workflow did not produce a final status.",
        )

        summary = self.require_result(
            graph_result.get("summary"),
            "The workflow did not produce a summary.",
        )

        result = GLControllerWorkflowResult(
            correlation_id=correlation_id,
            general_ledger_result=general_ledger_result,
            controller_result=controller_result,
            final_status=final_status,
            summary=summary,
        )

        return self.validate_workflow_result(result)