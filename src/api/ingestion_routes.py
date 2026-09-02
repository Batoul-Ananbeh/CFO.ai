"""Dataset ingestion API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.database.repositories.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
)
from src.application.models import (
    CFOAnalysisResponse,
)
from src.ingestion.models import (
    DatasetIngestionRequest,
    DatasetIngestionResponse,
)
from src.ingestion.aggregation import (
    MonthlyAggregationResponse,
    MonthlyAggregationService,
)
from src.ai.factory import create_llm_provider
from src.application.persistence import (
    AnalysisPersistenceService,
)
from src.database.unit_of_work import (
    PersistenceUnitOfWork,
)
from src.ingestion.company_report import (
    CompanyCFOReportRequest,
    CompanyCFOReportService,
)
from src.ingestion.service import (
    DatasetMappingConflictError,
    DatasetIngestionService,
)


router = APIRouter(
    prefix="/api/v1/ingestion",
    tags=["Dataset Ingestion"],
)


def get_dataset_ingestion_service() -> DatasetIngestionService:
    """Build the deterministic ingestion service."""

    return DatasetIngestionService()


def get_monthly_aggregation_service() -> MonthlyAggregationService:
    """Build the deterministic monthly aggregation service."""

    return MonthlyAggregationService()


def get_company_cfo_report_service() -> CompanyCFOReportService:
    """Build the persistent company-report service."""

    unit_of_work_factory = (
        lambda: PersistenceUnitOfWork()
    )

    return CompanyCFOReportService(
        aggregation=MonthlyAggregationService(
            unit_of_work_factory=unit_of_work_factory
        ),
        provider=create_llm_provider(),
        persistence=AnalysisPersistenceService(
            unit_of_work_factory=unit_of_work_factory
        ),
    )


@router.post(
    "/datasets",
    response_model=DatasetIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": (
                "The ingestion correlation ID already exists."
            ),
        },
    },
)
def ingest_dataset(
    request: DatasetIngestionRequest,
    service: Annotated[
        DatasetIngestionService,
        Depends(get_dataset_ingestion_service),
    ],
) -> DatasetIngestionResponse:
    """Validate and stage a canonical JSON or CSV dataset."""

    try:
        return service.ingest(request)
    except DuplicateRecordError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_INGESTION_CORRELATION_ID",
                "message": (
                    "An ingestion batch with this correlation ID "
                    "already exists."
                ),
                "correlation_id": request.correlation_id,
            },
        ) from None
    except DatasetMappingConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DATASET_MAPPING_CONFLICT",
                "message": str(exc),
                "company_code": request.company_code,
            },
        ) from None


@router.get(
    "/batches/{batch_id}",
    response_model=DatasetIngestionResponse,
    status_code=status.HTTP_200_OK,
)
def get_ingestion_batch(
    batch_id: str,
    service: Annotated[
        DatasetIngestionService,
        Depends(get_dataset_ingestion_service),
    ],
) -> DatasetIngestionResponse:
    """Return an ingestion result for Dashboard polling and history."""

    try:
        return service.get_batch(
            batch_id
        )
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "INGESTION_BATCH_NOT_FOUND",
                "message": "The ingestion batch was not found.",
                "batch_id": batch_id,
            },
        ) from None


@router.get(
    "/batches/{batch_id}/monthly-summaries",
    response_model=MonthlyAggregationResponse,
    status_code=status.HTTP_200_OK,
)
def get_monthly_summaries(
    batch_id: str,
    service: Annotated[
        MonthlyAggregationService,
        Depends(get_monthly_aggregation_service),
    ],
) -> MonthlyAggregationResponse:
    """Return currency-safe company and branch monthly summaries."""

    try:
        return service.aggregate(
            batch_id
        )
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "INGESTION_BATCH_NOT_FOUND",
                "message": "The ingestion batch was not found.",
                "batch_id": batch_id,
            },
        ) from None


@router.post(
    "/batches/{batch_id}/cfo-report",
    response_model=CFOAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def create_company_cfo_report(
    batch_id: str,
    request: CompanyCFOReportRequest,
    service: Annotated[
        CompanyCFOReportService,
        Depends(get_company_cfo_report_service),
    ],
) -> CFOAnalysisResponse:
    """Generate and persist a batch-level company CFO report."""

    try:
        return service.generate(
            batch_id=batch_id,
            report_request=request,
        )
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "INGESTION_BATCH_NOT_FOUND",
                "message": "The ingestion batch was not found.",
                "batch_id": batch_id,
            },
        ) from None
    except DuplicateRecordError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_CORRELATION_ID",
                "message": (
                    "An analysis with this correlation ID already exists."
                ),
                "correlation_id": request.correlation_id,
            },
        ) from None
