# Threat Model

## 1. Scope

This threat model covers:

- the Chrome extension;
- manually supplied sponsor-register CSV files;
- the ingestion pipeline;
- locally stored processed datasets;
- any future static dataset distribution endpoint.

## 2. Protected assets

| Asset | Why it matters |
|---|---|
| Dataset integrity | Incorrect data could mislead job-search decisions |
| User browsing privacy | Job searches can reveal sensitive personal circumstances |
| Selected company text | Should not be transmitted unnecessarily |
| Extension integrity | Compromise could expose browsing data |
| Build and release credentials | Could allow malicious releases |
| Source provenance | Needed to demonstrate government-source fidelity |

## 3. Trust boundaries

```text
GOV.UK file
  → administrator device
  → ingestion pipeline
  → processed dataset
  → extension package/storage
  → webpage result card
```

Every boundary must treat incoming content as untrusted.

## 4. Principal threats and controls

| Threat | Risk | Control |
|---|---|---|
| Malformed or manipulated CSV | Corrupt or misleading results | Schema, checksum, row-count and content validation |
| CSV formula injection | Dangerous spreadsheet interpretation | Never execute cells; treat fields as plain text |
| HTML/script content in company name | Page injection or XSS | Escape all user and dataset text before rendering |
| Excessive Chrome permissions | Unnecessary access to user browsing | Request minimum permissions; user-triggered execution |
| Collection of browsing history | Privacy breach | No page-history logging; no full-page transmission |
| Remote code execution | Store-policy and security risk | Bundle executable code; no remote scripts or `eval` |
| Dependency compromise | Malicious package code | Lock dependencies, audit, minimise packages |
| Dataset rollback or tampering | Stale or manipulated licence status | Version, checksum and source metadata |
| Weak fuzzy matching | False sponsor claim | Conservative thresholds and ambiguity state |
| Source impersonation | Unofficial file accepted | Manual provenance check plus recorded source metadata |
| Release-account compromise | Malicious extension update | MFA, restricted access and signed store process |
| Logging sensitive text | Privacy leakage | Exclude selected text from production telemetry |

## 5. Chrome extension controls

- Use Manifest V3.
- Limit permissions to the documented minimum.
- Do not request access to all websites unless a validated feature requires it.
- Trigger processing only after explicit user action.
- Keep matching local where practical.
- Apply a strict content security policy.
- Do not use `eval`, dynamic script generation or remote executable code.
- Sanitize or escape every value inserted into a webpage.
- Ensure the result card cannot access page-level JavaScript state unnecessarily.

## 6. Data pipeline controls

- Accept only `.csv` input through the documented command.
- Verify required headers before processing rows.
- Calculate SHA-256 checksum.
- Never modify the raw source file.
- Write processed output to a new versioned path.
- Publish atomically only after all tests pass.
- Retain the last known valid dataset.
- Produce a machine-readable and human-readable validation report.

## 7. Privacy posture

The MVP should not collect:

- user identity;
- account information;
- browsing history;
- complete job descriptions;
- selected text history;
- application activity;
- CV or immigration data.

Any future analytics must undergo a separate privacy and threat review.

## 8. Abuse and misuse considerations

The product can be misunderstood as confirming willingness to sponsor. Controls:

- show a persistent disclaimer;
- use “found on the register” rather than “will sponsor”;
- expose official entity and route details;
- distinguish missing data from a definitive negative conclusion;
- provide the dataset date.

## 9. Residual risks

The extension cannot fully eliminate:

- changes made by the government after the latest manual update;
- brand-to-legal-entity ambiguity;
- incorrect employer names in recruiter postings;
- employers holding a licence but declining to sponsor a role;
- government source errors.

These limitations must be reflected in product language.
