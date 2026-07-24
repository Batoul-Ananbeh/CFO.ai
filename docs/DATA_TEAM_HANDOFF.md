# CFO.ai Data Team Handoff

## Mission

Prepare four separate Kaggle-based demo companies. Do not merge unrelated
datasets and claim that they came from one real company.

| Demo company | Dataset focus | Primary demonstration |
|---|---|---|
| `DEMO-GL` | General ledger | Accounting and control |
| `DEMO-ERP` | ERP sales and expenses | Operations and forecasting |
| `DEMO-FS` | Financial statements | Executive CFO reporting |
| `DEMO-RISK` | Financial anomalies | Risk and internal audit |

## First approved source

The first source is `general_ledger_source.xlsx`.

Verified workbook facts:

- Sheets: `GL`, `Chart of Accounts`, `Calendar`, `Territory`,
  `CashFlow_St`, and `SoCE_St`.
- `GL` contains 27,909 data rows.
- Dates cover 2018-01-01 through 2020-12-31.
- Seven territories are represented.
- GL account and territory keys resolve to their lookup sheets.
- The source does not expose canonical debit and credit columns directly.

Do not guess debit and credit mapping from the sign of `Amount`. Document the
source accounting convention and prove the mapping before producing canonical
transactions.

## Required canonical output

Return UTF-8 CSV using the exact header in:

`docs/templates/canonical_transactions_template.csv`

Every row must contain:

- a unique transaction ID;
- ISO transaction date and matching accounting period;
- one positive amount;
- one ISO 4217 currency;
- stable company and branch mapping;
- different debit and credit accounts;
- verified account types when classification is claimed.

## Required delivery per company

```text
demo_company_code/
  source/
    original_source_file
  output/
    canonical_transactions.csv
  mapping/
    account_mapping.csv
    branch_mapping.csv
    category_mapping.csv
  evidence/
    source_url.txt
    license.txt
    transformation_notes.md
    validation_report.json
```

## Validation report

`validation_report.json` must contain:

```json
{
  "company_code": "DEMO-GL",
  "source_row_count": 0,
  "output_row_count": 0,
  "rejected_row_count": 0,
  "duplicate_transaction_ids": 0,
  "unmapped_accounts": [],
  "unmapped_branches": [],
  "unmapped_categories": [],
  "currencies": [],
  "period_start": "YYYY-MM",
  "period_end": "YYYY-MM",
  "classification_coverage": 0.0,
  "mapping_assumptions": []
}
```

## Dataset completion rules

Mark `dataset_scope` as `company_complete` only when:

- all expected branches are present;
- the declared period range has no missing month;
- there are at least three periods;
- no source row is silently discarded;
- every debit and credit account type is verified;
- rejected rows equal zero.

Otherwise use `transaction_sample`. The backend will still ingest and display
the data, but will correctly block unsupported forecasting and strategy.

## Prohibited actions

- Do not edit backend, database, Agent, or API files.
- Do not place API keys or Kaggle tokens in the repository.
- Do not overwrite original source files.
- Do not combine currencies.
- Do not fabricate missing transactions, account types, branches, or dates.
- Do not label Kaggle data as real customer data.

## Final handoff checklist

- [ ] Original source and Kaggle URL included.
- [ ] License captured.
- [ ] Canonical CSV uses the exact contract.
- [ ] All mapping files included.
- [ ] Validation report has no unexplained difference in row counts.
- [ ] Transformation decisions are reproducible.
- [ ] No secret or personal information is present.
