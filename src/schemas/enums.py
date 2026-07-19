"""Shared enumerations used across CFO.ai schemas and agents."""

from enum import StrEnum


class AgentName(StrEnum):
    FINANCIAL_CONTROLLER = "financial_controller_agent"
    GENERAL_LEDGER = "general_ledger_agent"
    TREASURY = "treasury_agent"
    FPA = "fpa_agent"
    RISK_INTERNAL_AUDIT = "risk_internal_audit_agent"
    FINANCE_OPERATIONS = "finance_operations_agent"
    CHIEF_CFO = "chief_cfo_agent"


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ControllerDecisionStatus(StrEnum):
    APPROVED = "APPROVED"
    APPROVED_WITH_WARNINGS = "APPROVED_WITH_WARNINGS"
    REQUIRES_CORRECTION = "REQUIRES_CORRECTION"
    REQUIRES_HUMAN_APPROVAL = "REQUIRES_HUMAN_APPROVAL"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ReportType(StrEnum):
    TRIAL_BALANCE = "trial_balance"
    BANK_RECONCILIATION = "bank_reconciliation"
    ACCOUNTS_PAYABLE = "accounts_payable"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    PAYROLL = "payroll"
    FINANCIAL_STATEMENT = "financial_statement"
    JOURNAL_ENTRY = "journal_entry"


class ValidationCheckStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"