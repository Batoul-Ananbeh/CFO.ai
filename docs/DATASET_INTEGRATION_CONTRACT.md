# CFO.ai Dataset Integration Contract v1.0

## Scope

This contract connects multi-company demo datasets to CFO.ai without making
industry-specific assumptions. One ingestion batch belongs to one company and
may contain transactions from multiple branches.

Ingestion is deterministic. It does not call an LLM.

## Endpoint

`POST /api/v1/ingestion/datasets`

`GET /api/v1/ingestion/batches/{batch_id}` returns the persisted result for
Dashboard polling or history views.

The endpoint accepts either:

- JSON records through `records`, with `source_format: "json"`; or
- UTF-8 CSV text through `csv_content`, with `source_format: "csv"`.

Exactly one source payload must be supplied.

## Batch fields

| Field | Required | Meaning |
|---|---:|---|
| `correlation_id` | Yes | Unique idempotency key for the ingestion attempt |
| `company_code` | Yes | Stable company business code |
| `company_name` | Yes | Display name |
| `base_currency` | Yes | Three-character currency code |
| `source_name` | Yes | Original logical filename |
| `source_format` | Yes | `json` or `csv` |

## Canonical transaction columns

| Column | Rule |
|---|---|
| `transaction_id` | Required and unique inside the dataset |
| `transaction_date` | ISO date: `YYYY-MM-DD` |
| `accounting_period` | `YYYY-MM`; must match transaction date |
| `transaction_category` | CFO.ai `TransactionCategory` value |
| `description` | Non-empty business description |
| `amount` | Decimal value greater than zero |
| `currency` | Three-character currency code |
| `branch_code` | Stable branch code |
| `branch_name` | Branch display name |
| `debit_account_code` | Required account code |
| `debit_account_name` | Required account name |
| `debit_account_type` | Optional verified type: ASSET, LIABILITY, EQUITY, REVENUE, or EXPENSE |
| `credit_account_code` | Required account code, different from debit |
| `credit_account_name` | Required account name |
| `credit_account_type` | Optional verified account type |

## Result semantics

- `COMPLETED`: every row validated.
- `PARTIAL`: at least one row validated and at least one was rejected.
- `FAILED`: no rows validated.

Rejected rows remain in staging with public validation errors. They are never
silently discarded or promoted to trusted financial reporting.

## Dashboard integration

The Dashboard should display:

- batch status;
- total, accepted, and rejected rows;
- mapped branch codes;
- row-level validation errors;
- the batch ID used by later aggregation endpoints.

## Monthly aggregation

`GET /api/v1/ingestion/batches/{batch_id}/monthly-summaries`

The endpoint returns separate company and branch summaries for every
accounting period and currency. Different currencies are never added together.

Transactions without verified debit and credit account types remain visible in
transaction counts, but they do not contribute to classified revenue,
expenses, assets, liabilities, or equity.

Forecast and Strategy capabilities are enabled only when:

- the dataset declares `company_complete`;
- expected branches exactly match observed branches;
- the full declared reporting-period range is present;
- at least three periods are present;
- no source rows were rejected; and
- account-type classification coverage is 100%.

## Company CFO report

`POST /api/v1/ingestion/batches/{batch_id}/cfo-report`

Request:

```json
{
  "correlation_id": "COMPANY-REPORT-001",
  "request": "Prepare a verified company CFO report."
}
```

When the data profile is complete, the report executes:

1. Risk AI
2. Forecast AI
3. Strategy AI
4. Chief CFO AI

General Ledger and Controller are not run on monthly aggregate data because
their current deterministic workflow validates an individual journal entry.

If evidence is insufficient, no LLM call is made. CFO.ai persists a
deterministic `INSUFFICIENT_DATA` report containing the exact limitations.

If an AI provider fails, execution stops at that agent and persists one
structured provider error without generating misleading dependency failures.

## Next contract

The next backend increment will consume `VALIDATED` staging records and create
monthly company and branch financial summaries. Only that validated
aggregation layer may issue a verified `data_profile` that enables Forecast
and Strategy agents.
