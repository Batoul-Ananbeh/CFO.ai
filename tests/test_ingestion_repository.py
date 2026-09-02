"""Ingestion repository and unit-of-work tests."""

from __future__ import annotations

import pytest

from src.database.base import Base
from src.database.repositories.errors import DuplicateRecordError
from src.database.session import create_database_engine, create_session_factory
from src.database.settings import DatabaseSettings
from src.database.unit_of_work import PersistenceUnitOfWork


def build_database():
    """Create an isolated ingestion repository database."""

    engine = create_database_engine(
        DatabaseSettings(url="sqlite+pysqlite:///:memory:")
    )
    Base.metadata.create_all(engine)
    return engine, create_session_factory(engine)


def test_ingestion_repository_persists_complete_provenance():
    engine, session_factory = build_database()

    with PersistenceUnitOfWork(session_factory) as unit_of_work:
        company = unit_of_work.companies.create(
            code="PHARMA-GROUP",
            name="Pharmacy Group",
        )
        branch = unit_of_work.branches.create(
            company_id=company.id,
            code="MAIN",
            name="Main Branch",
        )
        batch = unit_of_work.ingestion.create_batch(
            company_id=company.id,
            correlation_id="INGEST-REPO-001",
            manifest={"total_files": 1},
        )
        source_file = unit_of_work.ingestion.add_source_file(
            batch_id=batch.id,
            branch_id=branch.id,
            branch_code=branch.code,
            file_name="main.dmp",
            extension=".dmp",
            byte_size=2048,
            sha256="c" * 64,
        )
        unit_of_work.ingestion.add_staging_record(
            batch_id=batch.id,
            source_file_id=source_file.id,
            branch_id=branch.id,
            entity_type="sale",
            source_row_number=1,
            source_key="SALE-001",
            raw_payload={"amount": "25.00"},
        )
        batch_id = batch.id
        company_id = company.id

    with PersistenceUnitOfWork(session_factory) as unit_of_work:
        stored = unit_of_work.ingestion.get_batch(batch_id)
        batches = unit_of_work.ingestion.list_batches_for_company(company_id)

        assert stored is not None
        assert len(stored.source_files) == 1
        assert len(stored.staging_records) == 1
        assert stored.source_files[0].branch_code == "MAIN"
        assert stored.staging_records[0].raw_payload == {
            "amount": "25.00"
        }
        assert [batch.id for batch in batches] == [batch_id]

    engine.dispose()


def test_ingestion_repository_rejects_duplicate_file_hash():
    engine, session_factory = build_database()

    with pytest.raises(DuplicateRecordError):
        with PersistenceUnitOfWork(session_factory) as unit_of_work:
            company = unit_of_work.companies.create(
                code="DUPLICATE-FILE",
                name="Duplicate File",
            )
            batch = unit_of_work.ingestion.create_batch(
                company_id=company.id,
                correlation_id="INGEST-DUPLICATE-FILE",
                manifest={},
            )
            arguments = {
                "batch_id": batch.id,
                "branch_code": "MAIN",
                "file_name": "main.dmp",
                "extension": ".dmp",
                "byte_size": 1,
                "sha256": "d" * 64,
            }
            unit_of_work.ingestion.add_source_file(**arguments)
            unit_of_work.ingestion.add_source_file(**arguments)

    engine.dispose()
