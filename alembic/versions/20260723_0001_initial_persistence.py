"""Create initial CFO.ai persistence tables.

Revision ID: 20260723_0001
Revises:
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260723_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial CFO.ai persistence schema."""

    op.create_table(
        "companies",
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "base_currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_companies",
        ),
        sa.UniqueConstraint(
            "code",
            name="uq_companies_code",
        ),
    )

    op.create_index(
        "ix_companies_code",
        "companies",
        ["code"],
        unique=True,
    )

    op.create_table(
        "branches",
        sa.Column(
            "company_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "external_reference",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_branches_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_branches",
        ),
        sa.UniqueConstraint(
            "company_id",
            "code",
            name="uq_branches_company_code",
        ),
    )

    op.create_index(
        "ix_branches_company_id",
        "branches",
        ["company_id"],
        unique=False,
    )

    op.create_table(
        "analyses",
        sa.Column(
            "company_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "correlation_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "request_text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "financial_input",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "execution_plan",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "executed_agents",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "verified_results",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "ai_results",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "final_agent",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "final_output",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "errors",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_analyses_branch_id_branches",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_analyses_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_analyses",
        ),
        sa.UniqueConstraint(
            "correlation_id",
            name="uq_analyses_correlation_id",
        ),
    )

    op.create_index(
        "ix_analyses_branch_id",
        "analyses",
        ["branch_id"],
        unique=False,
    )

    op.create_index(
        "ix_analyses_company_id",
        "analyses",
        ["company_id"],
        unique=False,
    )

    op.create_index(
        "ix_analyses_correlation_id",
        "analyses",
        ["correlation_id"],
        unique=True,
    )

    op.create_index(
        "ix_analyses_status",
        "analyses",
        ["status"],
        unique=False,
    )

    op.create_table(
        "agent_executions",
        sa.Column(
            "analysis_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "agent_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "sequence_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "input_payload",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "output_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "error_category",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "provider_status_code",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "retryable",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "prompt_tokens",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "output_tokens",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "total_tokens",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "thought_tokens",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name="fk_agent_executions_analysis_id_analyses",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_agent_executions",
        ),
        sa.UniqueConstraint(
            "analysis_id",
            "sequence_number",
            name="uq_agent_executions_analysis_sequence",
        ),
    )

    op.create_index(
        "ix_agent_executions_agent_name",
        "agent_executions",
        ["agent_name"],
        unique=False,
    )

    op.create_index(
        "ix_agent_executions_analysis_id",
        "agent_executions",
        ["analysis_id"],
        unique=False,
    )

    op.create_index(
        "ix_agent_executions_status",
        "agent_executions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column(
            "company_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "branch_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "analysis_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "actor_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name="fk_audit_logs_analysis_id_analyses",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_audit_logs_branch_id_branches",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_audit_logs_company_id_companies",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_audit_logs",
        ),
    )

    op.create_index(
        "ix_audit_logs_action",
        "audit_logs",
        ["action"],
        unique=False,
    )

    op.create_index(
        "ix_audit_logs_analysis_id",
        "audit_logs",
        ["analysis_id"],
        unique=False,
    )

    op.create_index(
        "ix_audit_logs_branch_id",
        "audit_logs",
        ["branch_id"],
        unique=False,
    )

    op.create_index(
        "ix_audit_logs_company_id",
        "audit_logs",
        ["company_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the initial CFO.ai persistence schema."""

    op.drop_index(
        "ix_audit_logs_company_id",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_branch_id",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_analysis_id",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_action",
        table_name="audit_logs",
    )

    op.drop_table("audit_logs")

    op.drop_index(
        "ix_agent_executions_status",
        table_name="agent_executions",
    )

    op.drop_index(
        "ix_agent_executions_analysis_id",
        table_name="agent_executions",
    )

    op.drop_index(
        "ix_agent_executions_agent_name",
        table_name="agent_executions",
    )

    op.drop_table("agent_executions")

    op.drop_index(
        "ix_analyses_status",
        table_name="analyses",
    )

    op.drop_index(
        "ix_analyses_correlation_id",
        table_name="analyses",
    )

    op.drop_index(
        "ix_analyses_company_id",
        table_name="analyses",
    )

    op.drop_index(
        "ix_analyses_branch_id",
        table_name="analyses",
    )

    op.drop_table("analyses")

    op.drop_index(
        "ix_branches_company_id",
        table_name="branches",
    )

    op.drop_table("branches")

    op.drop_index(
        "ix_companies_code",
        table_name="companies",
    )

    op.drop_table("companies")
