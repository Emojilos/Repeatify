# Shkolkovo Parser

The parser package lives in `backend/scripts/shkolkovo_parser/` and prepares
public Shkolkovo problem data for the Repeatify backend. The MVP pipeline covers
catalog parsing, problem parsing, text normalization, validation, image download,
JSON export, reports, and debug artifacts.

The default workflows use bundled offline fixtures. Plain HTTP is used only for
pages that are explicitly reachable without JavaScript. Discovery for
`https://3.shkolkovo.online/catalog?SubjectId=1` showed a JavaScript browser
check, so live work against the official target host requires a Playwright-backed
browser smoke before any larger collection.

## Setup

Install parser dependencies:

```text
uv sync --group parser
```

Install Chromium only for the Playwright live browser scenario:

```text
uv run --group parser playwright install chromium
```

## Commands

Offline fixture test run:

```text
uv run --group parser python -m scripts.shkolkovo_parser --mode test
```

Single task fixture run:

```text
uv run --group parser python -m scripts.shkolkovo_parser --mode test --task-number 6
```

Per-subcategory fixture limit:

```text
uv run --group parser python -m scripts.shkolkovo_parser --mode test --task-number 6 --per-subcategory 1
```

All available fixture catalogs:

```text
uv run --group parser python -m scripts.shkolkovo_parser --mode all
```

Controlled live smoke:

```text
uv run --group parser python -m scripts.shkolkovo_parser --task-number 6 --max-pages 1 --max-problems 3 --debug
```

The live smoke is intentionally separate from the unit-test suite. It must follow
the access-stop rules in `DISCOVERY.md` and may produce a blocked report when the
official site returns a browser check, CAPTCHA, 429, repeated 403, or another
access limitation.

## Generated Paths

Generated parser files are written under `data/raw/shkolkovo/` relative to the
repository root:

- `task_N.json` contains exported dataset records.
- `task_N_errors.json` contains parse, validation, fetch, and image errors.
- `task_N_report.json` contains per-task counters and status.
- `run_report_YYYYMMDD_HHMMSS.json` contains aggregate all-mode counters plus
  partial and failed records for manual review.
- `html/` contains saved HTML snapshots.
- `images/task_N/` contains downloaded problem images.
- `debug/task_N/` contains raw and intermediate debug artifacts when `--debug`
  is used.

The generated dataset, snapshots, reports, images, and debug directories are not
intended to be committed. `data/raw/shkolkovo/README.md` remains as the tracked
directory marker.

## MVP Limits

The MVP does not import data into Supabase. It only writes local JSON files and
reports for review.

The parser collects only public unauthenticated content. It must not use
credentials, cookies, authorization headers, CAPTCHA bypasses, paywall bypasses,
or rate-limit bypasses. If content is closed or protected, the run must stop and
record the reason in errors or reports instead of trying to work around the
restriction.
