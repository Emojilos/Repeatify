# Shkolkovo Parser

The MVP parser defaults to offline fixture workflows and plain HTTP for pages
that are explicitly reachable without JavaScript. Discovery for
`https://3.shkolkovo.online/catalog?SubjectId=1` showed a JavaScript browser
check, so live work against the official target host requires a Playwright-backed
browser smoke before any larger collection.

Install parser dependencies:

```text
uv sync --group parser
```

Install Chromium only for the Playwright live browser scenario:

```text
uv run --group parser playwright install chromium
```

Offline fixture smoke:

```text
uv run --group parser python -m scripts.shkolkovo_parser --mode test
```

Live browser-backed smoke is intentionally separate from the unit-test suite and
must still follow the access-stop rules in `DISCOVERY.md`.
