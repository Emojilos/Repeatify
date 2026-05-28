# Shkolkovo Public Access Discovery

Date: 2026-05-28

## Scope

This note records the access decision for the MVP parser before implementing any
live fetch layer. The parser must only use pages and fields visible to an
ordinary unauthenticated visitor. It must not use credentials, session cookies,
authorization headers, CAPTCHA bypasses, paywall bypasses, or rate-limit bypasses.

## Checked Sources

- Target from PRD: `https://3.shkolkovo.online/catalog?SubjectId=1`
- Official platform site: `https://shkolkovoonline.ru/`
- Official user agreement: `https://shkolkovoonline.ru/files/agreement.pdf`
- Public indexed problem page observed during discovery:
  `https://giashka.ru/ОГЭ/математика/задания/тип-1/задача_9d8ab69f-80b0-44ea-9a83-7fe9e235f4b1`
- Public robots file for the indexed problem host: `https://giashka.ru/robots.txt`

## Findings

The official agreement describes `https://3.shkolkovo.online` as the public site
for the platform, states that registration is not required for the theoretical
knowledge base and free problem catalog, and describes the problem catalog as a
free open collection where users can solve tasks and check answers.

Direct HTTP access to the official target host is not currently sufficient for
the parser:

```text
$ curl -L -A 'Mozilla/5.0 ... Chrome/125 Safari/537.36' \
>   https://3.shkolkovo.online/catalog?SubjectId=1
HTTP/2 503
body contains: "Ваш браузер не смог пройти проверку"
body contains: "включите ... поддержку JavaScript"
```

The same browser-check response was returned for:

```text
https://3.shkolkovo.online/robots.txt
```

Because `robots.txt` for the official target host could not be retrieved without
passing the same JavaScript browser check, the live parser must treat official
robots status as unknown until checked in an ordinary browser session. A failed
robots fetch must not be ignored by a full collector.

An indexed public task page on `giashka.ru` was reachable without credentials and
without CAPTCHA during this discovery. Its server-rendered HTML contained the
task ID, problem text, image URL, answer value, type metadata, and source fields.
That page also references Shkolkovo-hosted image/API URLs. The host's robots file
returned:

```text
User-Agent: *
Allow: /
Disallow: /панель-администратора/
Disallow: /%D0%BF%D0%B0%D0%BD%D0%B5%D0%BB%D1%8C-%D0%B0%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80%D0%B0/
Disallow: /platform-admin-panel
```

This confirms that HTTP parsing is technically possible for at least one public
indexed problem representation, but it is not enough to approve HTTP-first
collection from the official `3.shkolkovo.online` target host.

## Fetch Strategy Decision

Use browser-required live discovery for the official Shkolkovo target before any
mass collection from `3.shkolkovo.online`.

The initial fetch layer may still be implemented HTTP-first for offline fixtures,
saved snapshots, tests, and public pages that are explicitly reachable by plain
HTTP. However, a live full run against the official target host must require a
browser-backed smoke check first, because direct HTTP currently receives a
JavaScript browser-check page instead of catalog content.

## Playwright Dependency Decision

TASK-028 treats the JavaScript browser check above as confirmed need for a
browser-backed fallback path. The `parser` dependency group therefore includes
`playwright`, and Chromium setup is intentionally documented as an explicit
operator step instead of being hidden in normal unit-test or fixture workflows.

Install the browser runtime only for live browser-backed smoke/discovery:

```text
uv run --group parser playwright install chromium
```

## Safety Rules For Later Tasks

- Do not accept credentials, cookies, or authorization headers.
- Stop immediately on HTTP 429, repeated 403, CAPTCHA, or browser-check pages
  that do not resolve in an ordinary browser.
- Keep default delays conservative and avoid parallel HTML page fetching.
- Record access failures in reports instead of trying alternate bypass methods.
- Before full live collection, re-check `robots.txt` in a normal browser context
  and document the result in the run report.
- Do not use the `giashka.ru` indexed page as a silent replacement for the
  official target source without a separate product decision.
