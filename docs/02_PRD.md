# Product Requirements Document

## 1. Product objective

Build a Chrome extension that allows a user to select a company name on a webpage and check whether a matching organisation appears on the official UK Register of Licensed Sponsors.

## 2. User job to be done

> When I find a UK job and need sponsorship, I want to check the employer immediately so that I can decide whether the role is worth deeper investigation without leaving the job page.

## 3. User stories

| ID | User story | Priority |
|---|---|---|
| US-01 | As a user, I can highlight a company name and initiate a sponsor check. | Must |
| US-02 | As a user, I can see whether an exact official register match exists. | Must |
| US-03 | As a user, I can see sponsor route, rating and location for the match. | Must |
| US-04 | As a user, I can distinguish exact, probable, ambiguous and not-found results. | Must |
| US-05 | As a user, I can see when the dataset was last updated. | Must |
| US-06 | As a user, I can open the official government source for verification. | Must |
| US-07 | As an administrator, I can process a newly downloaded CSV through one documented command. | Must |
| US-08 | As an administrator, I am warned when the source schema or record volume is abnormal. | Must |
| US-09 | As a user, the lookup continues to work using the last valid dataset if an update fails. | Should |
| US-10 | As a user, I can copy or save a matched company result. | Could |

## 4. Primary user journey

1. User opens a job page.
2. User highlights the employer name in the posting or job description.
3. User right-clicks and selects **Check UK sponsorship**.
4. Extension reads only the selected text.
5. Matching engine normalises and searches the sponsor dataset.
6. Extension displays a compact result card.
7. User reviews the legal entity, location, sponsor route and confidence.
8. User may open the official source or dismiss the card.

## 5. Functional requirements

### 5.1 Selection and invocation

- The extension must add a context-menu action.
- The action must be available when text is selected.
- Empty selections must not trigger a lookup.
- Input must be length-limited and treated as untrusted text.
- The extension must not read the full page unless a future approved feature requires it.

### 5.2 Matching

The matching engine must:

- preserve the original user input;
- create a normalised search form;
- attempt exact normalised matching first;
- attempt approved alias matching second;
- attempt conservative fuzzy matching only after exact methods fail;
- use town/city only as a secondary disambiguation signal;
- never treat a missing county as a failed match;
- return multiple candidates where confidence is insufficient.

### 5.3 Result states

| State | Definition | Required wording |
|---|---|---|
| Exact | One high-confidence normalised or alias match | Licensed sponsor found |
| Probable | One strong but non-exact candidate | Possible sponsor match — verify entity |
| Ambiguous | Multiple plausible candidates | Multiple registered entities found |
| Not found | No candidate exceeds threshold | No matching organisation found in the current register |
| Error | Dataset unavailable or lookup fails | Unable to verify using the current dataset |

### 5.4 Result content

Each result must show, where available:

- official organisation name;
- town/city;
- county;
- type and rating;
- one or more routes;
- match confidence or result category;
- dataset publication or processing date;
- official source label;
- disclaimer.

### 5.5 Disclaimer

The interface must state:

> Register presence confirms that a matching organisation holds a sponsor licence. It does not confirm that the employer will sponsor this vacancy or applicant.

### 5.6 Data administration

The ingestion workflow must:

- accept a CSV file path;
- validate required columns;
- validate file type and encoding;
- compare record count with the previous accepted version;
- reject malformed or materially incomplete files;
- preserve the original source file checksum;
- transform the data into the product dataset;
- generate metadata;
- retain the previous valid version;
- create a human-readable validation report.

## 6. Non-functional requirements

| Dimension | Requirement |
|---|---|
| Performance | Cached lookup should normally complete within 500 ms |
| Privacy | No browsing history, full page content or job description may be transmitted |
| Reliability | Last valid dataset remains available after a failed update |
| Accessibility | Keyboard operable; readable contrast; semantic labels |
| Maintainability | Ingestion, matching and UI modules remain separable |
| Security | Minimum Chrome permissions; no remote executable code |
| Auditability | Every published dataset has date, source identifier and checksum |
| Compatibility | Support the current stable Chrome release using Manifest V3 |

## 7. Acceptance criteria

The MVP is accepted when:

1. A user can highlight text on a standard webpage and invoke the extension.
2. Known exact sponsors return the correct legal entity and routes.
3. Non-sponsors are not falsely labelled as licensed sponsors.
4. Ambiguous names display multiple candidates rather than one fabricated answer.
5. Dataset age and source are visible.
6. The extension continues to work without a network connection after installation or dataset caching.
7. The ingestion command rejects a CSV missing any required source field.
8. Automated tests cover normalisation, matching, ingestion and the principal result states.
9. Chrome permissions are limited to the documented minimum.
10. The privacy statement accurately reflects implemented behaviour.

## 8. Initial success metrics

| Metric | Initial purpose |
|---|---|
| Median lookup time | Measures workflow improvement |
| Exact-match rate | Indicates how often the selected name maps directly |
| Ambiguous-result rate | Highlights entity-resolution gaps |
| False-positive rate | Protects user trust |
| Manual correction examples | Builds alias and test datasets |
| Weekly repeat usage | Indicates recurring utility |
| Dataset age | Measures operational freshness |

## 9. Future candidates

- automatic employer-name detection on supported job sites;
- user-maintained company watchlists;
- trading-name alias library;
- role-level sponsorship evidence;
- automation of official file acquisition;
- support for Firefox and Edge.
