"""Pharmacy ingestion persistence-model tests."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database.base import Base
from src.database.models import (
    Branch,
    Company,
    IngestionBatch,
    IngestionSourceFile,
    StagingRecord,
)
from src.database.session import create_database_engine, create_session_factory
from src.database.settings import DatabaseSettings


def build_database():
    """Create an isolated ingestion database."""

    engine = create_database_engine(
        DatabaseSettings(url="sqlite+pysqlite:///:memory:")
    )
    Base.metadata.create_all(engine)
    return engine, create_session_factory(engine)


def test_ingestion_metadata_contains_staging_tables():
    engine, _ = build_database()

    assert set(Base.metadata.tables) >= {
        "ingestion_batches",
        "ingestion_source_files",
        "staging_records",
    }

    engine.dispose()


def test_raw_record_preserves_branch_and_file_provenance():
    engine, session_factory = build_database()

    company = Company(
        code="PHARMA-GROUP",
        name="Pharmacy Group",
        base_currency="JOD",
    )
    branch = Branch(
        company=company,
        code="MAIN",
        name="Main Branch",
    )
    batch = IngestionBatch(
        company=company,
        correlation_id="INGEST-001",
        manifest={"total_files": 1},
    )
    source_file = IngestionSourceFile(
        batch=batch,
        branch=branch,
        branch_code="MAIN",
        file_name="main.dmp",
        extension=".dmp",
        byte_size=1024,
        sha256="a" * 64,
        source_metadata={},
    )
    staging_record = StagingRecord(
        batch=batch,
        source_file=source_file,
        branch=branch,
        entity_type="sale",
        source_row_number=1,
        source_key="SALE-001",
        raw_payload={"amount": "10.00"},
    )

    with session_factory() as session:
        session.add_all([company, branch, batch, source_file, staging_record])
        session.commit()

        stored = session.scalar(select(StagingRecord))

        assert stored is not None
        assert stored.batch.correlation_id == "INGEST-001"
        assert stored.source_file.branch_code == "MAIN"
        assert stored.raw_payload == {"amount": "10.00"}
        assert stored.normalized_payload is None
        assert stored.status == "RAW"

    engine.dispose()


def test_source_row_is_unique_within_file_and_entity():
    engine, session_factory = build_database()

    company = Company(code="UNIQUE-INGEST", name="Unique Ingest")
    batch = IngestionBatch(
        company=company,
        correlation_id="INGEST-UNIQUE",
        manifest={},
    )
    source_file = IngestionSourceFile(
        batch=batch,
        branch_code="MAIN",
        file_name="main.dmp",
        extension=".dmp",
        byte_size=1,
        sha256="b" * 64,
        source_metadata={},
    )
    first = StagingRecord(
        batch=batch,
        source_file=source_file,
        entity_type="product",
        source_row_number=1,
        raw_payload={},
    )
    duplicate = StagingRecord(
        batch=batch,
        source_file=source_file,
        entity_type="product",
        source_row_number=1,
        raw_payload={},
    )

    with session_factory() as session:
        session.add_all([company, batch, source_file, first, duplicate])

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("Duplicate staged source row should fail.")

    engine.dispose()
