"""Factories for the CFO.ai application layer."""

from __future__ import annotations

from src.ai.factory import create_llm_provider
from src.ai.provider import LLMProvider
from src.ai.settings import AISettings
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.application.service import (
    CFOApplicationService,
)
from src.database.session import (
    SessionFactory,
)
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.planning.dynamic_planner import (
    DynamicCFOPlanner,
)
from src.runtime.deterministic_runner import (
    build_gl_controller_cfo_runtime,
)
from src.workflows.gl_controller_workflow import (
    GLControllerWorkflow,
)


def build_cfo_application_service(
    *,
    provider: LLMProvider | None = None,
    settings: AISettings | None = None,
    workflow: GLControllerWorkflow | None = None,
    planner: DynamicCFOPlanner | None = None,
    persistence: (
        AnalysisPersistenceService | None
    ) = None,
    persistence_enabled: bool = False,
    session_factory: SessionFactory | None = None,
) -> CFOApplicationService:
    """
    Build the production CFO application service.

    Persistence remains optional for tests and embedded consumers.
    The live HTTP API enables it explicitly.
    """

    selected_provider = (
        provider
        if provider is not None
        else create_llm_provider(
            settings=settings
        )
    )

    runtime = build_gl_controller_cfo_runtime(
        provider=selected_provider,
        workflow=workflow,
        planner=planner,
    )

    selected_persistence = persistence

    if (
        selected_persistence is None
        and persistence_enabled
    ):
        def unit_of_work_factory() -> (
            PersistenceUnitOfWork
        ):
            return PersistenceUnitOfWork(
                session_factory=session_factory
            )

        selected_persistence = (
            AnalysisPersistenceService(
                unit_of_work_factory=(
                    unit_of_work_factory
                )
            )
        )

    return CFOApplicationService(
        runtime=runtime,
        persistence=selected_persistence,
    )