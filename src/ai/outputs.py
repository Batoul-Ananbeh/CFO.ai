"""Structured output models shared by CFO.ai agents."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FinancialExplanation(BaseModel):
    """Structured explanation generated from verified financial data."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        min_length=1,
        description="Clear summary based only on verified context.",
    )

    key_points: list[str] = Field(
        default_factory=list,
        description="Important verified findings and interpretations.",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommended review or follow-up actions.",
    )


class ControllerReview(BaseModel):
    """Structured AI explanation of a financial control review."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)

    control_findings: list[str] = Field(
        default_factory=list,
    )

    required_corrections: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class RiskAssessment(BaseModel):
    """Structured financial and internal-control risk assessment."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)

    risk_level: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    risk_findings: list[str] = Field(
        default_factory=list,
    )

    missing_information: list[str] = Field(
        default_factory=list,
    )

    recommended_controls: list[str] = Field(
        default_factory=list,
    )


class ForecastAnalysis(BaseModel):
    """Structured explanation of a verified financial forecast."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)

    assumptions: list[str] = Field(
        default_factory=list,
    )

    expected_scenario: list[str] = Field(
        default_factory=list,
    )

    downside_risks: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class StrategyAnalysis(BaseModel):
    """Structured financial strategy recommendations."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)

    strategic_priorities: list[str] = Field(
        default_factory=list,
    )

    recommended_actions: list[str] = Field(
        default_factory=list,
    )

    expected_benefits: list[str] = Field(
        default_factory=list,
    )

    risks_and_tradeoffs: list[str] = Field(
        default_factory=list,
    )


class ChiefCFOBrief(BaseModel):
    """Executive financial brief produced by the Chief CFO Agent."""

    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=1)

    key_financial_signals: list[str] = Field(
        default_factory=list,
    )

    critical_risks: list[str] = Field(
        default_factory=list,
    )

    recommended_decisions: list[str] = Field(
        default_factory=list,
    )

    human_approvals_required: list[str] = Field(
        default_factory=list,
    )