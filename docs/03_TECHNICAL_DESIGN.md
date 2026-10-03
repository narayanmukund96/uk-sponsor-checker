# Technical Design Document

## 1. Architecture summary

The MVP consists of three independent systems:

1. **Manual source acquisition** — the administrator downloads the CSV from GOV.UK.
2. **Local ingestion pipeline** — validates, normalises, aggregates and publishes a product dataset.
3. **Chrome extension** — accepts selected text, performs matching and displays results.

```text
Official GOV.UK CSV
        ↓ manual download
Local ingestion command
        ↓
Validation report + processed dataset + metadata
        ↓
Bundled or static versioned dataset
        ↓
Chrome extension local cache
        ↓
Selection → matching engine → result card
```

## 2. Recommended technology stack

| Layer | Recommendation |
|---|---|
| Extension language | TypeScript |
| UI | React with minimal component set, or vanilla TypeScript for a smaller build |
| Extension framework | Plasmo or Vite + CRXJS |
| Manifest | Chrome Manifest V3 |
| Storage | `chrome.storage.local`; IndexedDB if dataset size requires it |
| Search | Custom exact indexes plus a conservative fuzzy library |
| Ingestion | Python 3 with pandas or Python CSV tooling |
| Testing | Vitest, Pytest and Playwright |
| Packaging | npm scripts plus Chrome extension packaging |
| Version control | Git and public GitHub repository |
| CI | GitHub Actions for tests and build checks; not initially for source acquisition |

## 3. Component design

### 3.1 Ingestion module

Responsibilities:

- read the manually downloaded CSV;
- validate schema and record count;
- clean whitespace and encoding;
- retain official values;
- create normalised search keys;
- aggregate repeated organisation records;
- produce a deterministic JSON dataset;
- produce dataset metadata and validation output;
- retain rollback copies.

Suggested files:

```text
ingestion/
├── cli.py
├── schema.py
├── validate.py
├── normalize.py
├── aggregate.py
├── publish.py
└── models.py
```

### 3.2 Matching module

Responsibilities:

- normalise selected user text;
- search exact-name index;
- search alias index;
- search suffix-stripped index;
- calculate conservative fuzzy candidates;
- rank candidates;
- return structured match state and evidence.

The matching module must be independent of Chrome APIs so it can be unit-tested and reused.

### 3.3 Extension service worker

Responsibilities:

- register the context-menu item;
- receive selected text;
- load or access the dataset index;
- invoke the matching module;
- send the result to the active tab.

### 3.4 Content script

Responsibilities:

- receive a structured result;
- render a sandboxed result card;
- escape all displayed source and user text;
- support dismissal and keyboard access;
- avoid modifying unrelated page behaviour.

### 3.5 Dataset storage

Preferred MVP options:

| Option | Advantages | Trade-off |
|---|---|---|
| Bundle dataset with extension | Fully offline and simplest security model | Extension update required for each data refresh |
| Host versioned static dataset | Data can update without full extension release | Requires network access, integrity checks and hosting |
| Manual local file load | Useful only during development | Poor end-user experience |

For a personal MVP, bundle the dataset. For public beta, move to a signed or checksum-verified static dataset.

## 4. Data structures

### 4.1 Sponsor entity

```ts
interface SponsorEntity {
  id: string;
  officialName: string;
  normalizedName: string;
  aliases: string[];
  townCity: string | null;
  county: string | null;
  licences: Array<{
    typeAndRating: string;
    route: string;
  }>;
}
```

### 4.2 Dataset metadata

```ts
interface DatasetMetadata {
  sourceName: string;
  sourceFileName: string;
  processedAt: string;
  sourceDate: string | null;
  rawRowCount: number;
  entityCount: number;
  sha256: string;
  schemaVersion: string;
  dataVersion: string;
}
```

### 4.3 Match result

```ts
type MatchState = "exact" | "probable" | "ambiguous" | "not_found" | "error";

interface MatchResult {
  state: MatchState;
  input: string;
  normalizedInput: string;
  candidates: Array<{
    sponsorId: string;
    score: number;
    reasons: string[];
  }>;
  datasetVersion: string;
}
```

## 5. Matching sequence

```text
Selected text
    ↓
Input validation
    ↓
Normalisation
    ↓
Exact normalised index
    ↓ no result
Alias index
    ↓ no result
Suffix-stripped exact index
    ↓ no result
Conservative fuzzy candidate generation
    ↓
Confidence and ambiguity rules
    ↓
Structured result
```

Fuzzy matching must not run across every record on every lookup. Build precomputed indexes or candidate buckets to keep performance predictable.

## 6. Permissions

Initial manifest permissions should be limited to:

- `contextMenus`
- `storage`
- `activeTab`
- `scripting` only if required for result injection

No blanket host permissions should be requested for the MVP.

## 7. Error handling

| Failure | Required behaviour |
|---|---|
| Invalid selected text | Show a concise input error |
| Dataset missing | Show unavailable state |
| Dataset malformed | Reject at ingestion; never publish |
| Search exception | Log locally and show generic error |
| Result-card injection failure | Fall back to extension popup or notification |
| Update failure | Continue using the last valid dataset |

## 8. Observability

For the personal MVP:

- structured local development logs;
- ingestion validation reports;
- test outputs;
- optional local error log.

For a public version:

- privacy-preserving crash monitoring;
- no selected company text in telemetry by default;
- explicit event taxonomy and data-retention policy.

## 9. Build commands

Suggested command contract:

```bash
npm run dev
npm run build
npm run test
npm run test:e2e
python -m ingestion.cli update --input /path/to/register.csv
python -m ingestion.cli validate --input /path/to/register.csv
```

## 10. Future automation seam

The source acquisition layer must expose a simple contract:

```text
Input: path or stream containing the official CSV
Output: immutable raw file for ingestion
```

A future automated downloader can replace manual acquisition without changing validation, transformation, matching or extension code.
