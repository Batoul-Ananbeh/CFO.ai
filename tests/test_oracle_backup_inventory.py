"""Oracle backup inventory tests."""

from __future__ import annotations

from hashlib import sha256

import pytest

from src.ingestion.inventory import (
    build_backup_inventory,
    inspect_backup_file,
)


def test_inspect_backup_file_records_identity(tmp_path):
    content = b"safe-oracle-dump-fixture"
    backup = tmp_path / "main_branch.dmp"
    backup.write_bytes(content)

    item = inspect_backup_file(
        backup,
        branch_code=" main ",
    )

    assert item.branch_code == "MAIN"
    assert item.file_name == "main_branch.dmp"
    assert item.byte_size == len(content)
    assert item.sha256 == sha256(content).hexdigest()


def test_inventory_is_ordered_and_totals_bytes(tmp_path):
    first = tmp_path / "first.dmp"
    second = tmp_path / "second.dmp"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    manifest = build_backup_inventory(
        {
            "branch-02": second,
            "branch-01": first,
        }
    )

    assert [item.branch_code for item in manifest.items] == [
        "BRANCH-01",
        "BRANCH-02",
    ]
    assert manifest.total_files == 2
    assert manifest.total_bytes == 11


def test_inventory_rejects_missing_backup(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_backup_inventory(
            {"MAIN": tmp_path / "missing.dmp"}
        )


def test_inventory_rejects_non_dmp_file(tmp_path):
    backup = tmp_path / "backup.zip"
    backup.write_bytes(b"not-a-dump")

    with pytest.raises(ValueError, match=".dmp extension"):
        inspect_backup_file(
            backup,
            branch_code="MAIN",
        )
