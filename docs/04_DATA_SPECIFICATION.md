# Data Specification

## 1. Source

Source file reviewed:

`SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-07-21.csv`

Observed structure:

| Attribute | Value |
|---|---:|
| Raw rows | 142,534 |
| Source columns | 5 |
| Missing organisation names | 0 |
| Missing town/city | 2 |
| Missing county | 94,505 |
| Repeated organisation-name rows | 15,329 |

## 2. Source fields

| Source field | Meaning | Product treatment |
|---|---|---|
| Organisation Name | Official register organisation text | Preserve exactly; create separate search keys |
| Town/City | Registered location indicator | Preserve; use for display and disambiguation |
| County | Optional location indicator | Preserve when present; never require for matching |
| Type & Rating | Sponsor category and rating | Preserve; optionally parse into separate fields |
| Route | Approved immigration route | Preserve and aggregate across repeated records |

## 3. Core transformation principle

Never overwrite official source values. Store:

1. the original official field;
2. separately derived normalised fields used only for search and matching.

## 4. Organisation-name normalisation

Create `normalized_name` through a deterministic sequence:

1. Unicode normalisation.
2. Convert to lowercase.
3. Trim leading and trailing whitespace.
4. Collapse repeated internal whitespace.
5. Replace punctuation with spaces where safe.
6. Standardise ampersand and “and” representation.
7. Remove legal suffixes only in a separate `base_name` field.
8. Detect trading-name markers such as `T/A`, `TA`, `trading as` and preserve both legal and trading forms.
9. Generate aliases without deleting the official name.
10. Avoid semantic rewriting or AI-generated aliases in the MVP.

### Example

```text
Official:
BRANOS OXFORD LTD T/A LILO

normalized_name:
branos oxford ltd t a lilo

base_name:
branos oxford

aliases:
- branos oxford
- lilo
- branos oxford lilo
```

## 5. Legal suffix handling

The following may be removed only from `base_name`, not from the official value:

- limited
- ltd
- plc
- llp
- incorporated
- inc
- company
- co

Suffix removal must be position-aware and conservative. Do not remove tokens where they form part of a distinctive trading name.

## 6. Location normalisation

For town/city and county:

- preserve source value;
- trim whitespace;
- collapse duplicate spaces;
- normalise case for comparison;
- do not infer missing county;
- do not treat county absence as a negative signal;
- use location only to distinguish otherwise similar organisations.

## 7. Type and rating mapping

Preserve `Type & Rating` exactly and optionally derive:

```text
sponsor_type:
- Worker
- Temporary Worker

rating:
- A rating
- B rating
- A (Premium)
- A (SME+)
- UK Expansion Worker: Provisional
```

Parsing failures must leave the official source value intact and create a validation warning.

## 8. Route mapping

Observed route values should be trimmed and mapped to canonical internal identifiers while preserving labels.

Example:

| Source label | Canonical ID |
|---|---|
| Skilled Worker | `skilled_worker` |
| Scale-up | `scale_up` |
| Charity Worker | `charity_worker` |
| Creative Worker | `creative_worker` |
| Global Business Mobility: Senior or Specialist Worker | `gbm_senior_specialist_worker` |

The extension should display the official or approved user-facing label, not the internal ID.

## 9. Record aggregation

The source may repeat an organisation because it holds multiple routes or licence categories.

Recommended grouping key:

```text
official organisation name
+ town/city
+ county when present
```

Within each grouped entity:

- retain all unique type/rating and route pairs;
- remove exact duplicate pairs;
- preserve deterministic ordering;
- do not merge same-name organisations across different towns unless a later verified entity-resolution rule supports it.

## 10. Search indexes

Generate:

| Index | Key | Purpose |
|---|---|---|
| Official exact | Normalised official name | Highest-confidence match |
| Base exact | Legal-suffix-stripped name | Common brand/legal variation |
| Alias exact | Trading name or curated alias | Brand-to-entity matching |
| Token index | Distinctive tokens | Candidate generation |
| Location index | Normalised town/city | Secondary disambiguation |

## 11. Match confidence

| Result | Minimum evidence |
|---|---|
| Exact | Unique official, base-name or approved alias match |
| Probable | Strong fuzzy similarity with no close competing candidate |
| Ambiguous | Multiple candidates within the ambiguity margin |
| Not found | No candidate crosses the minimum threshold |

Threshold values must be calibrated against a reviewed golden dataset and must not be selected arbitrarily.

## 12. Data quality validations

Reject publication when:

- any required column is missing;
- organisation name contains unexpected nulls;
- row count falls outside the configured tolerance;
- the file cannot be decoded reliably;
- output contains duplicate IDs;
- aggregation loses source rows unexpectedly;
- metadata or checksum generation fails.

Warn, but do not necessarily reject, when:

- town/city is blank;
- county is blank;
- a new route or type/rating appears;
- unusually large additions or removals occur.

## 13. Versioning

Each processed dataset must include:

- schema version;
- source filename;
- source date where known;
- processing timestamp;
- SHA-256 checksum;
- raw row count;
- aggregated entity count;
- previous data version.

## 14. Manual update contract

The administrator supplies an unedited official CSV. The pipeline performs all validation and transformation. Manual spreadsheet editing is not part of the approved process.
