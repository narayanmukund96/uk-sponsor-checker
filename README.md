# UK Sponsor Checker

Privacy-first prototype for checking selected company text against a locally processed copy of the official UK Register of Licensed Sponsors.

## Current milestone

This repository currently implements:

- the ingestion and matching prototype;
- a vanilla Manifest V3 Chrome extension MVP for local testing.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Validate a source CSV

```powershell
python -m ingestion.cli validate --input C:\path\to\register.csv
```

## Publish a processed dataset

```powershell
python -m ingestion.cli update --input C:\path\to\register.csv --output data\processed\sponsors.json --report data\reports\validation-report.json
```

The command preserves official source values, generates search-only normalised values, aggregates repeated licence rows, writes metadata, and rejects malformed inputs before publication.

## Refresh from GOV.UK

Run a live dry run to confirm the current GOV.UK CSV can be found:

```powershell
python scripts\refresh_from_govuk.py --dry-run
```

Run the full refresh:

```powershell
python scripts\refresh_from_govuk.py
```

The refresh command downloads the current GOV.UK CSV, validates it against the existing dataset, writes a versioned raw CSV, writes a versioned processed JSON file, writes a validation report, and promotes the new JSON to both `data\processed\sponsors.json` and `extension\data\sponsors.json` only if validation passes.

To install a weekly Windows refresh task:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_weekly_govuk_refresh.ps1
```

By default it runs every Monday at 09:30 and logs to `data\logs\weekly-refresh.log`.

## Test the Chrome extension MVP

1. Confirm `extension\data\sponsors.json` exists.
2. Open Chrome and go to `chrome://extensions`.
3. Enable Developer mode.
4. Choose **Load unpacked**.
5. Select the `extension` folder.
6. Open `extension\test-page.html` in Chrome.
7. Highlight a company name, right-click and choose **Check UK sponsorship**.

The extension uses `contextMenus`, `activeTab`, `scripting` and `storage` permissions, reads only the selected text, and performs matching locally against the bundled dataset.

With the full 3 October 2026 register, the first lookup may take a few seconds while Chrome loads and indexes the bundled dataset. Subsequent cached lookups are expected to be near-instant during the same service-worker session.

After changing extension files, remove and reload the unpacked extension in `chrome://extensions`; Chrome does not automatically pick up every local file change.

The matcher supports partial company selections. It checks full exact names first, then approved aliases and base names, then conservative brand-token and ordered partial-token matches. Partial matches are shown as probable unless competing entities make the result ambiguous.

Domain-like selections are also handled. For inputs such as `microsoft.com`, `jobs.microsoft.com` or `careers.creatio.com`, the matcher derives the registrable company label and searches that as an additional form. The result still depends on the official register dataset; an absent domain owner remains not found.

Result cards are colour-coded by state: exact matches use green, probable matches use blue, ambiguous matches use amber, not-found results use red, and errors use grey.
