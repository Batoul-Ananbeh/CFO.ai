# CFO.ai — Phase 2 Verification Report

Date: 2026-07-23

## Scope

This verification covered the delivered source archive without using a `.env`
file or external AI credentials. No Git commit or push was performed.

## Verified successfully

- A clean Python environment can be created from `requirements.txt`.
- The complete automated suite passes: `133 passed`.
- The previous Starlette `TestClient` deprecation warning is resolved by the
  declared `httpx2` test dependency.
- Alembic upgrades a clean SQLite verification database to
  `20260723_0001 (head)`.
- The migrated database contains:
  - `companies`
  - `branches`
  - `analyses`
  - `agent_executions`
  - `audit_logs`
  - `alembic_version`
- The database connectivity/schema check succeeds.
- Focused API and persistence tests pass: `31 passed`.
- A live local Uvicorn smoke test confirms:
  - `GET /health` returns HTTP 200.
  - `GET /api/v1/agents` returns HTTP 200 and six agents.
  - an unknown analysis returns HTTP 404.
- The persisted-analysis detail test returns HTTP 200 and includes token usage.
- AI usage extraction and persistence tests pass.

## Dependency corrections

- Replaced the invalid UTF-16 `requirements.txt` with a UTF-8 direct-dependency
  manifest.
- Added the missing `langgraph` dependency.
- Added direct runtime, API, database, and test dependencies.
- Added `requirements-legacy.txt` for the unused pre-orchestrator LangChain
  agents.
- Removed UTF-8 BOM markers from affected configuration and Python files.

## Environment limitations

The verification environment does not provide Docker and does not contain the
user's live PostgreSQL volume. Therefore it could not reproduce the historical
PostgreSQL record identified by:

```text
f9d9f7a8-f74c-4d62-9cea-965b1d81dda7
```

The historical live `500 Internal Server Error` for that specific record is
not considered resolved until the endpoint is re-run against the original
PostgreSQL data and its traceback is captured if it fails again.

Likewise, automated verification proves that token columns are extracted,
stored, and returned, but the latest original PostgreSQL row still requires a
read-only check on the user's machine.

## Phase decision

Phase 2 is code-complete and passes all isolated automated verification.

Operational closure remains pending only for:

1. PostgreSQL container health on the original machine.
2. Alembic current/head confirmation on the original PostgreSQL database.
3. Re-testing the latest persisted analysis detail endpoint.
4. Confirming live token columns for `general_ledger_ai`.
5. Reviewing the real Git working tree before an approved local commit.

Do not start Phase 3 or create a commit until these five operational checks are
completed and approved.
