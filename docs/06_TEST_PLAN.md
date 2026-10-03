# Test Plan

## 1. Objective

Validate that the ingestion pipeline, matching engine and Chrome extension produce accurate, secure and understandable results across common and difficult company-name scenarios.

## 2. Test layers

| Layer | Framework | Scope |
|---|---|---|
| Data validation | Pytest | Source schema, nulls, row counts, mappings |
| Unit tests | Pytest/Vitest | Normalisation, aggregation, scoring |
| Integration tests | Vitest/Pytest | Dataset generation through match result |
| Extension tests | Playwright | Context menu, messaging and result card |
| Manual exploratory | Chrome | Real job pages and edge cases |
| Security checks | Dependency and static analysis | Permissions, injection, unsafe APIs |

## 3. Golden dataset

Create a reviewed test file with at least:

| Category | Initial cases |
|---|---:|
| Exact legal-name matches | 100 |
| Legal suffix variations | 50 |
| Trading-name/alias matches | 50 |
| Same-name organisations in different locations | 50 |
| Ambiguous names | 50 |
| Genuine not-found companies | 100 |
| Malicious or malformed input strings | 25 |

Each case must define:

- user input;
- expected state;
- expected entity or candidates;
- expected confidence category;
- reason for the expected outcome.

## 4. Ingestion tests

| Test | Expected result |
|---|---|
| Valid current CSV | Accepted and transformed |
| Missing required column | Rejected |
| Unexpected new column | Accepted with informational note unless conflicting |
| Null organisation name | Rejected |
| Blank county | Accepted |
| Blank town/city | Warning |
| Abnormally low row count | Rejected |
| Duplicate source rows | Deduplicated or reported according to rule |
| Unknown route | Preserved and warning generated |
| Reprocessing same file | Deterministic identical output |
| Encoding irregularity | Safely decoded or rejected with clear error |

## 5. Normalisation tests

Cover:

- case differences;
- punctuation;
- repeated whitespace;
- ampersand versus “and”;
- legal suffixes;
- `T/A` and “trading as” forms;
- apostrophes and hyphens;
- Unicode characters;
- short company names;
- names containing common words such as “group”, “services” or “UK”.

## 6. Matching tests

| Scenario | Expected behaviour |
|---|---|
| Unique exact official match | Exact |
| Unique suffix-stripped match | Exact or high-confidence exact |
| Verified trading alias | Exact |
| Strong fuzzy match with clear separation | Probable |
| Two similar candidates | Ambiguous |
| Weak fuzzy similarity | Not found |
| Matching name, different towns | Multiple candidates or location-assisted result |
| Missing county | No penalty |
| Recruiter name selected instead of employer | Correctly checks recruiter only; no inference |
| Empty or very long selection | Input error |

## 7. UI tests

- context-menu item appears only when relevant;
- selected text reaches the matching engine;
- all five result states render correctly;
- long names wrap without breaking layout;
- result card is keyboard accessible;
- focus is managed correctly;
- source and disclaimer are visible;
- user can dismiss the card;
- unsafe HTML renders as text;
- the extension does not obstruct the underlying webpage.

## 8. Browser and page tests

Test on:

- LinkedIn job detail page;
- recruiter-authored LinkedIn posting;
- Indeed job page;
- company career page;
- ordinary text webpage;
- dynamically rendered single-page application;
- page with restrictive styles and high z-index components.

## 9. Failure tests

| Failure | Expected response |
|---|---|
| Dataset unavailable | Error state, no fabricated result |
| Corrupt local dataset | Error state and logged diagnostic |
| Content-script injection denied | Popup or clear fallback |
| No network | Cached/bundled lookup still works |
| Update rejected | Previous valid dataset remains active |
| New source schema | Pipeline stops and explains mismatch |

## 10. Security tests

- inject `<script>` and HTML payloads in selected text;
- inject HTML-like content in a test dataset;
- verify no use of `eval`;
- inspect manifest permissions;
- verify no selected text is sent over the network;
- inspect package for remote scripts;
- run dependency audit;
- test oversized and malformed input.

## 11. Exit criteria

A release candidate may proceed when:

- all must-have acceptance criteria pass;
- no critical or high-severity security issue remains;
- exact-match golden tests pass at 100%;
- approved alias tests pass at 100%;
- false-positive rate remains within the agreed threshold;
- ambiguous scenarios do not resolve as false exact matches;
- ingestion rollback is tested;
- privacy documentation matches implementation.
