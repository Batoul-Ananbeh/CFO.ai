"""Pharmacy data-ingestion foundations for CFO.ai."""

from src.ingestion.inventory import (
    BackupInventoryItem,
    BackupInventoryManifest,
    build_backup_inventory,
    inspect_backup_file,
)
from src.ingestion.models import (
    CanonicalTransactionRow,
    DatasetIngestionRequest,
    DatasetIngestionResponse,
    IngestionRowError,
)
from src.ingestion.aggregation import (
    AggregationDataProfile,
    FinancialTotals,
    MonthlyAggregationResponse,
    MonthlyAggregationService,
    MonthlyFinancialSummary,
)
from src.ingestion.company_report import (
    CompanyCFOReportRequest,
    CompanyCFOReportService,
)
from src.ingestion.service import (
    DatasetMappingConflictError,
    DatasetIngestionService,
)

__all__ = [
    "BackupInventoryItem",
    "BackupInventoryManifest",
    "AggregationDataProfile",
    "CanonicalTransactionRow",
    "CompanyCFOReportRequest",
    "CompanyCFOReportService",
    "DatasetIngestionRequest",
    "DatasetIngestionResponse",
    "DatasetIngestionService",
    "DatasetMappingConflictError",
    "IngestionRowError",
    "FinancialTotals",
    "MonthlyAggregationResponse",
    "MonthlyAggregationService",
    "MonthlyFinancialSummary",
    "build_backup_inventory",
    "inspect_backup_file",
]
