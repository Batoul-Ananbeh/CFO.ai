# MVP Cost Optimization Changelog

## Baseline

- Source commit: `1c4324a8`
- Baseline test result: 173 passed.

## Changes

- Added `economy`, `balanced`, and `full` company-report execution modes.
- Made `economy` the default, reducing the full report from four AI calls to
  two.
- Added deterministic company-report context compaction.
- Added aggregate token telemetry to the company-report response.
- Reduced default output-token and retry limits.
- Made structured-response attempts configurable and defaulted to one.
- Added configurable Gemini thinking levels and defaulted the MVP to
  `minimal`.
- Added Data and Dashboard team handoffs.
- Added the MVP delivery plan and canonical CSV template.
- Added raw-data ignore rules.

## Verification

- Full offline test suite: 176 passed.
- Economy plan: Risk then Chief CFO.
- Balanced plan: Risk, Forecast, then Chief CFO.
- Full plan: Risk, Forecast, Strategy, then Chief CFO.
- Incomplete evidence still returns deterministic `INSUFFICIENT_DATA` with no
  AI call.
