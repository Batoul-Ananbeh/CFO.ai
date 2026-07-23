"""Build a JSON inventory for pharmacy Oracle .dmp backups."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ingestion.inventory import build_backup_inventory


def _branch_assignment(value: str) -> tuple[str, Path]:
    """Parse BRANCH_CODE=PATH command-line assignments."""

    branch_code, separator, raw_path = value.partition("=")

    if not separator or not branch_code.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError(
            "Use BRANCH_CODE=PATH, for example MAIN=C:\\backups\\main.dmp"
        )

    return branch_code.strip(), Path(raw_path.strip())


def build_parser() -> argparse.ArgumentParser:
    """Create the backup inventory command parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Inventory Oracle Data Pump backups without exposing their data."
        )
    )
    parser.add_argument(
        "--branch",
        action="append",
        required=True,
        type=_branch_assignment,
        metavar="CODE=PATH",
        help="Repeat once per pharmacy branch.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("oracle_backup_inventory.json"),
        help="JSON manifest destination.",
    )
    return parser


def main() -> int:
    """Run backup inventory generation."""

    arguments = build_parser().parse_args()
    branch_backups = dict(arguments.branch)
    manifest = build_backup_inventory(branch_backups)

    arguments.output.write_text(
        json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Inventoried {manifest.total_files} backup file(s) "
        f"across {len(branch_backups)} branch(es)."
    )
    print(f"Manifest: {arguments.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
