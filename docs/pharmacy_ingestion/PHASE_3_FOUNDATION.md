# CFO.ai — Phase 3 Pharmacy Ingestion Foundation

## Objective

Load financial and operational data from four independent pharmacy Oracle
databases without trusting source quantities blindly or losing branch-level
provenance.

## Implemented Foundation

The first Phase 3 increment provides:

- a safe Oracle `.dmp` inventory command;
- streaming SHA-256 fingerprints for every backup;
- branch-to-file assignment;
- an auditable ingestion batch model;
- source-file provenance records;
- raw staging records with validation state;
- Alembic migration `20260723_0002`;
- isolated SQLite and full-suite automated tests.

## Data Flow

```text
Oracle .dmp per branch
        ↓
Backup inventory and SHA-256
        ↓
Ingestion batch
        ↓
Source file provenance
        ↓
Raw staging records
        ↓
Validation and normalization
        ↓
Reconciliation
        ↓
Trusted finance and reporting tables
```

No raw row is promoted directly into CFO reporting. Every staged row retains:

- ingestion batch;
- source file;
- branch;
- source entity type;
- source row number;
- original payload;
- normalized payload;
- validation errors;
- processing status.

## Backup Inventory Command

Run from the project root with the project virtual environment:

```powershell
.\venv\Scripts\python.exe -m scripts.inventory_oracle_backups `
    --branch MAIN="C:\path\main.dmp" `
    --branch BRANCH-02="C:\path\branch02.dmp" `
    --output ".\oracle_backup_inventory.json"
```

Repeat `--branch` for every available pharmacy backup.

The generated manifest contains file identity metadata, sizes, timestamps, and
hashes. It does not extract or print business rows.

## Required User Inputs for the Next Increment

The next implementation cannot safely infer the Oracle schema. It requires:

1. the generated `oracle_backup_inventory.json`;
2. the exact branch name/code corresponding to each `.dmp`;
3. Oracle database version if known;
4. export method if known: Data Pump `expdp` or legacy `exp`;
5. one representative backup or a schema-only export;
6. confirmation of which backups are missing or failed;
7. confirmation that the files may be processed in the development
   environment.

Do not send database passwords or place `.dmp` files in Git.

## Next Engineering Increment

After the inputs above are available:

1. detect dump format and Oracle version compatibility;
2. restore into an isolated Oracle environment;
3. extract table and column metadata;
4. identify sales, purchases, inventory, expenses, suppliers, products, and
   branch entities;
5. create explicit mapping profiles;
6. stream source rows into staging;
7. calculate per-table and financial control totals;
8. reconcile source totals before promotion.
