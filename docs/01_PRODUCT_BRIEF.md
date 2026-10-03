# Product Brief

## Product name

Working name: **UK Sponsor Checker**

## Problem

UK job seekers who require employer sponsorship must repeatedly leave job pages, search for the employer, compare company names against the official sponsor register and determine whether a matching legal entity exists. This process is slow, inconsistent and particularly difficult where recruiters post on behalf of another company or where the trading name differs from the registered legal entity.

## Target user

Primary user:

- A UK-based or UK-bound job seeker who requires Skilled Worker or another sponsored work route.

Initial use case:

- Reviewing jobs on LinkedIn and checking the employer without leaving the page.

## Product proposition

Allow the user to highlight or select a company name on a webpage and receive an immediate, source-grounded indication of whether a matching organisation appears on the official UK sponsor register.

## Core value

- Reduces repetitive manual checking.
- Keeps the user inside the job-search workflow.
- Uses the government register as the sole source of truth.
- Shows matching confidence rather than overstating certainty.
- Preserves privacy by avoiding collection of browsing history or complete job descriptions.

## MVP scope

The MVP will:

- accept user-selected text;
- normalise the selected company name;
- search a locally available sponsor dataset;
- return exact, probable, ambiguous or not-found results;
- display legal entity name, town/city, sponsor route, rating and dataset date;
- link the user back to the official source;
- use a manually downloaded government CSV processed through an automated local pipeline.

## Out of scope

The MVP will not:

- guarantee that an employer will sponsor a particular role;
- determine whether the role meets visa eligibility or salary requirements;
- automatically parse every job description;
- scrape LinkedIn search results at scale;
- collect job-search or browsing history;
- require a user account;
- use third-party sponsorship databases as the source of truth.

## Product principles

1. **Source fidelity:** preserve the official data without silently rewriting legal facts.
2. **Precision over recall:** avoid presenting weak fuzzy matches as confirmed sponsors.
3. **Transparent uncertainty:** distinguish exact, probable, ambiguous and not-found outcomes.
4. **Privacy by default:** perform matching locally where practical.
5. **Manual source, automated processing:** manually obtain the file, but validate and transform it programmatically.
6. **Automation-ready architecture:** future source automation must not require rebuilding the matching engine.

## Success definition

The MVP is successful when the user can check a company from a job page in under two seconds, understand the result correctly and avoid a separate Google or manual spreadsheet search in most cases.
