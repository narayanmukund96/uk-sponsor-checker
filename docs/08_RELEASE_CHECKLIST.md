# Release Checklist

## Product

- [ ] MVP scope matches the approved PRD.
- [ ] All result states use approved wording.
- [ ] Disclaimer is visible.
- [ ] Dataset date is visible.
- [ ] Official legal name and routes display correctly.
- [ ] No feature implies guaranteed sponsorship.

## Data

- [ ] Latest official CSV was manually downloaded.
- [ ] Source provenance was recorded.
- [ ] Required columns passed validation.
- [ ] Row-count tolerance passed.
- [ ] Unknown routes or ratings were reviewed.
- [ ] Output checksum and metadata were generated.
- [ ] Previous valid dataset is retained.
- [ ] Golden matching tests pass.

## Engineering

- [ ] Production build completes.
- [ ] Unit, integration and browser tests pass.
- [ ] No critical dependency vulnerability remains.
- [ ] Manifest V3 is valid.
- [ ] Permissions are limited to the approved set.
- [ ] No remote executable code is present.
- [ ] No debug secrets or local file paths remain.
- [ ] Extension works after browser restart.
- [ ] Offline or cached behaviour is confirmed.

## Security and privacy

- [ ] Selected text is not transmitted externally.
- [ ] Browsing history is not collected.
- [ ] User and dataset text is safely escaped.
- [ ] Content security policy is configured.
- [ ] Privacy policy matches actual behaviour.
- [ ] Store privacy disclosures match actual behaviour.
- [ ] Release account uses MFA.

## User experience

- [ ] Context-menu action is understandable.
- [ ] Loading and error states are clear.
- [ ] Result card works with keyboard navigation.
- [ ] Contrast and text sizes are acceptable.
- [ ] Long organisation names render correctly.
- [ ] Ambiguous results allow comparison.
- [ ] Source verification path works.

## Chrome Web Store

- [ ] Product name and description are final.
- [ ] Icons and screenshots are prepared.
- [ ] Single-purpose description is accurate.
- [ ] Permission justifications are prepared.
- [ ] Privacy policy is publicly accessible.
- [ ] Support contact is provided.
- [ ] Packaged extension was tested from the release artefact.
- [ ] Version number and release notes are updated.

## Post-release

- [ ] Rollback procedure is documented.
- [ ] Known limitations are recorded.
- [ ] User feedback channel is active.
- [ ] First dataset refresh date is scheduled.
- [ ] Decision log includes the release decision.
