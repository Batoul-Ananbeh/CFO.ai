# CFO.ai AI Cost Control

## Deterministic first

Ingestion, validation, monthly aggregation, account classification, and
financial totals run without an LLM. AI receives only verified summaries.

## Company report modes

| Mode | AI calls | Agents |
|---|---:|---|
| `economy` | 2 | Risk, Chief CFO |
| `balanced` | 3 | Risk, Forecast, Chief CFO |
| `full` | 4 | Risk, Forecast, Strategy, Chief CFO |

`economy` is the default MVP mode and avoids 50% of the full report's AI calls.
Actual token and monetary savings depend on provider usage and model pricing.

## Context reduction

The company report sends:

- full company monthly summaries;
- the evidence profile;
- deterministic branch totals grouped by branch and currency;
- only outputs from agents already executed in the selected mode.

It does not send every raw transaction or repeat every branch-month record.

## Provider limits

Recommended MVP environment:

```text
AI_TEMPERATURE=0
AI_RETRY_ATTEMPTS=2
AI_MAX_OUTPUT_TOKENS=1024
AI_STRUCTURED_RESPONSE_ATTEMPTS=1
```

Increase structured attempts only when response reliability justifies the
possible extra call.

## Measurement

Real provider usage is attached to each AI result and persisted per agent.
The company-report response also includes an aggregate usage summary under:

`verified_results.ai_cost_policy.usage`

Null means the provider did not report that metric. It never means zero.
