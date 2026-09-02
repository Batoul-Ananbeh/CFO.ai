# CFO.ai MVP Delivery Plan

## MVP outcome

The MVP demonstrates one complete, auditable company-analysis journey:

1. Ingest one canonical company dataset.
2. Persist the ingestion batch and rejected-row evidence.
3. Produce deterministic company and branch monthly summaries.
4. Refuse unsupported AI analysis when the evidence profile is incomplete.
5. Run a cost-controlled company CFO report when evidence is complete.
6. Persist the analysis, agent executions, errors, and token telemetry.
7. Return Dashboard-ready JSON through documented API endpoints.

## Team ownership

| Workstream | Owner | Backend contract |
|---|---|---|
| Kaggle datasets and mapping | Data teammate | `docs/DATA_TEAM_HANDOFF.md` |
| Dashboard and demo UI | Dashboard teammate | `docs/DASHBOARD_INTEGRATION_HANDOFF.md` |
| Backend, agents, reliability, token cost | System owner | This repository |

## Demo path

### 1. Readiness

`GET /health`

`GET /readiness`

The demo must not continue when `/readiness` reports `not_ready`.

### 2. Ingest a company

`POST /api/v1/ingestion/datasets`

The successful response supplies the `batch_id` used by every later step.

### 3. Show ingestion quality

`GET /api/v1/ingestion/batches/{batch_id}`

Display accepted and rejected rows. Do not hide validation failures.

### 4. Show deterministic financial results

`GET /api/v1/ingestion/batches/{batch_id}/monthly-summaries`

Display company trends, branch summaries, classification coverage, verified
capabilities, and limitations. Never add different currencies together.

### 5. Generate the CFO report

`POST /api/v1/ingestion/batches/{batch_id}/cfo-report`

Recommended MVP request:

```json
{
  "correlation_id": "DEMO-CFO-REPORT-001",
  "request": "Prepare an executive CFO report from verified company data.",
  "execution_mode": "economy"
}
```

The default `economy` mode makes two AI calls: Risk and Chief CFO. The response
contains `verified_results.ai_cost_policy` for the cost panel.

### 6. Show history and auditability

Use the analysis-history endpoints to display the persisted analysis and
per-agent token usage.

## Acceptance criteria

- Database schema is at Alembic head.
- Every committed test passes.
- No `.env`, API key, or raw confidential dataset is committed.
- One complete canonical dataset returns `COMPLETED`.
- An incomplete dataset returns deterministic `INSUFFICIENT_DATA` without an
  AI call.
- Economy mode runs no more than two company-report AI calls.
- Provider failure is returned as one structured error without a dependency
  error cascade.
- Dashboard never presents synthetic or Kaggle data as customer production
  data.

## Explicitly outside this MVP

- Direct Oracle `.dmp` restoration.
- Automatic arbitrary-column mapping by an LLM.
- Live bank or ERP connections.
- Payment release or autonomous journal posting.
- Production authentication and tenant billing.
