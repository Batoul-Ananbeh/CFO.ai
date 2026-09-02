# CFO.ai Dashboard Integration Handoff

## Required screens

### 1. System status

- `GET /health`
- `GET /readiness`

Show a clear blocked state when the database or AI configuration is not ready.

### 2. Company ingestion

- Submit canonical JSON or CSV to `POST /api/v1/ingestion/datasets`.
- Save the returned `batch_id`.
- Show total, accepted, rejected, and branch counts.
- Render row-level validation errors.

### 3. Financial overview

- Call `GET /api/v1/ingestion/batches/{batch_id}/monthly-summaries`.
- Display every currency separately.
- Show revenue, expenses, net income, balance-sheet movements, transaction
  count, classification coverage, capabilities, and limitations.

### 4. CFO report

- Call `POST /api/v1/ingestion/batches/{batch_id}/cfo-report`.
- Default the UI selector to `economy`.
- Allow `balanced` and `full`, with warnings that they issue more AI calls.
- Show verified facts separately from AI interpretation.
- Show provider errors without replacing verified deterministic results.

### 5. Cost panel

Read:

```text
verified_results.ai_cost_policy.execution_mode
verified_results.ai_cost_policy.planned_ai_calls
verified_results.ai_cost_policy.executed_ai_calls
verified_results.ai_cost_policy.mode_avoided_ai_calls
verified_results.ai_cost_policy.usage.prompt_tokens
verified_results.ai_cost_policy.usage.output_tokens
verified_results.ai_cost_policy.usage.total_tokens
verified_results.ai_cost_policy.usage.cached_tokens
verified_results.ai_cost_policy.usage.thought_tokens
```

Display `Not reported by provider` for null usage values. Do not convert token
counts to money until an approved model-price table exists.

## MVP visual order

1. Company selector.
2. Ingestion quality card.
3. Revenue, expense, and net-income trend.
4. Branch comparison grouped by currency.
5. Risk level and findings.
6. Chief CFO executive summary.
7. Cost-control and token-usage card.
8. Evidence limitations and human approvals.

## Safety rules

- Never add currencies together.
- Never hide rejected rows or limitations.
- Never label AI text as a verified accounting calculation.
- Never show `COMPLETED` as approval to post a journal or release payment.
