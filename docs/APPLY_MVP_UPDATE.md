# Apply the CFO.ai MVP Update

## Before copying files

Run from the CFO.ai repository:

```powershell
git branch --show-current
git status --short
```

Expected branch:

```text
feature/pharmacy-ingestion
```

Do not delete or replace `.env` or `Data/raw`.

## Apply

Extract `CFO_ai_MVP_update_files.zip`, then copy its contents into the CFO.ai
repository root and allow Windows to replace files with the same names.

The update contains complete replacement copies of every changed file and the
new documentation and tests.

## Verify

```powershell
python -m pytest -q
```

Expected:

```text
176 passed
```

Then inspect:

```powershell
git status --short
git diff --stat
```

## Commit

After the tests pass:

```powershell
git add .env.example .gitignore src docs tests
git commit -m "feat: add cost-optimized CFO MVP modes"
```

Do not add raw datasets, `.env`, ZIP files, or snapshot files.
