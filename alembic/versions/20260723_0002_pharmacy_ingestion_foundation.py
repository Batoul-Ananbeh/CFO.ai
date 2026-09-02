"""Add pharmacy ingestion and raw staging tables.

Revision ID: 20260723_0002
Revises: 20260723_0001
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260723_0002"
down_revision: str | None = "20260723_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_columns() -> list[sa.Column]:
    """Return shared UUID and timestamp columns."""

    return [
        sa.Column("id", sa.String(length=36), nullable=False),
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
    ]


def upgrade() -> None:
    """Create ingestion provenance and raw staging tables."""

    op.create_table(
        "ingestion_batches",
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_identity_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_ingestion_batches_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_batches"),
        sa.UniqueConstraint(
            "correlation_id",
            name="uq_ingestion_batches_correlation_id",
        ),
    )
    op.create_index(
        "ix_ingestion_batches_company_id",
        "ingestion_batches",
        ["company_id"],
    )
    op.create_index(
        "ix_ingestion_batches_correlation_id",
        "ingestion_batches",
        ["correlation_id"],
        unique=True,
    )
    op.create_index(
        "ix_ingestion_batches_status",
        "ingestion_batches",
        ["status"],
    )

    op.create_table(
        "ingestion_source_files",
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("branch_code", sa.String(length=50), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=20), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        *_identity_columns(),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ingestion_batches.id"],
            name="fk_ingestion_source_files_batch_id_ingestion_batches",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_ingestion_source_files_branch_id_branches",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_source_files"),
        sa.UniqueConstraint(
            "batch_id",
            "sha256",
            name="uq_ingestion_source_files_batch_hash",
        ),
    )
    op.create_index(
        "ix_ingestion_source_files_batch_id",
        "ingestion_source_files",
        ["batch_id"],
    )
    op.create_index(
        "ix_ingestion_source_files_branch_id",
        "ingestion_source_files",
        ["branch_id"],
    )
    op.create_index(
        "ix_ingestion_source_files_sha256",
        "ingestion_source_files",
        ["sha256"],
    )

    op.create_table(
        "staging_records",
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("source_file_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        *_identity_columns(),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ingestion_batches.id"],
            name="fk_staging_records_batch_id_ingestion_batches",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            ["ingestion_source_files.id"],
            name="fk_staging_records_source_file_id_ingestion_source_files",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_staging_records_branch_id_branches",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_staging_records"),
        sa.UniqueConstraint(
            "source_file_id",
            "entity_type",
            "source_row_number",
            name="uq_staging_records_source_entity_row",
        ),
    )
    op.create_index(
        "ix_staging_records_batch_id",
        "staging_records",
        ["batch_id"],
    )
    op.create_index(
        "ix_staging_records_source_file_id",
        "staging_records",
        ["source_file_id"],
    )
    op.create_index(
        "ix_staging_records_branch_id",
        "staging_records",
        ["branch_id"],
    )
    op.create_index(
        "ix_staging_records_entity_type",
        "staging_records",
        ["entity_type"],
    )
    op.create_index(
        "ix_staging_records_status",
        "staging_records",
        ["status"],
    )


def downgrade() -> None:
    """Remove ingestion provenance and raw staging tables."""

    op.drop_table("staging_records")
    op.drop_table("ingestion_source_files")
    op.drop_table("ingestion_batches")
