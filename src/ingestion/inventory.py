"""Create a safe, content-addressed inventory of Oracle backup files."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


_HASH_CHUNK_SIZE = 1024 * 1024


class BackupInventoryItem(BaseModel):
    """Metadata required to identify one branch backup without opening it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    branch_code: str
    file_name: str
    extension: str
    byte_size: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    modified_at: datetime

    @field_validator("branch_code")
    @classmethod
    def normalize_branch_code(cls, value: str) -> str:
        """Normalize a stable business branch code."""

        if not isinstance(value, str):
            raise TypeError("Branch code must be a string.")

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError("Branch code cannot be empty.")

        return normalized


class BackupInventoryManifest(BaseModel):
    """Auditable inventory for one collection of branch backups."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    created_at: datetime
    source_system: str = "oracle_datapump"
    items: tuple[BackupInventoryItem, ...]
    total_files: int = Field(ge=0)
    total_bytes: int = Field(ge=0)


def _hash_file(path: Path) -> str:
    """Return a streaming SHA-256 digest without loading the backup in RAM."""

    digest = sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def inspect_backup_file(
    path: str | Path,
    *,
    branch_code: str,
) -> BackupInventoryItem:
    """Validate and inventory one Oracle Data Pump backup."""

    resolved_path = Path(path).expanduser().resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Backup file was not found: {resolved_path}"
        )

    if not resolved_path.is_file():
        raise ValueError(
            f"Backup path must point to a file: {resolved_path}"
        )

    if resolved_path.suffix.lower() != ".dmp":
        raise ValueError(
            "Oracle backup files must use the .dmp extension."
        )

    file_stat = resolved_path.stat()

    if file_stat.st_size < 1:
        raise ValueError("Oracle backup file cannot be empty.")

    return BackupInventoryItem(
        branch_code=branch_code,
        file_name=resolved_path.name,
        extension=resolved_path.suffix.lower(),
        byte_size=file_stat.st_size,
        sha256=_hash_file(resolved_path),
        modified_at=datetime.fromtimestamp(
            file_stat.st_mtime,
            tz=timezone.utc,
        ),
    )


def build_backup_inventory(
    branch_backups: Mapping[str, str | Path],
) -> BackupInventoryManifest:
    """Build a deterministic inventory for unique pharmacy branches."""

    if not isinstance(branch_backups, Mapping):
        raise TypeError("Branch backups must be provided as a mapping.")

    normalized_codes: set[str] = set()
    items: list[BackupInventoryItem] = []

    for branch_code, backup_path in branch_backups.items():
        normalized_code = branch_code.strip().upper()

        if normalized_code in normalized_codes:
            raise ValueError(
                f"Duplicate branch code: {normalized_code!r}."
            )

        normalized_codes.add(normalized_code)
        items.append(
            inspect_backup_file(
                backup_path,
                branch_code=normalized_code,
            )
        )

    ordered_items = tuple(
        sorted(items, key=lambda item: item.branch_code)
    )

    return BackupInventoryManifest(
        created_at=datetime.now(timezone.utc),
        items=ordered_items,
        total_files=len(ordered_items),
        total_bytes=sum(item.byte_size for item in ordered_items),
    )
