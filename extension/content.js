(function () {
  "use strict";

  const CARD_ID = "uk-sponsor-checker-card";
  const DISCLAIMER = "Register presence confirms that a matching organisation holds a sponsor licence. It does not confirm that the employer will sponsor this vacancy or applicant.";

  const STATE_LABELS = {
    exact: "Licensed sponsor found",
    probable: "Possible sponsor match - verify entity",
    ambiguous: "Multiple registered entities found",
    not_found: "No matching organisation found in the current register",
    error: "Unable to verify using the current dataset"
  };

  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) element.textContent = String(text);
    return element;
  }

  function licenceText(entity) {
    const licences = entity.licences || [];
    if (!licences.length) return "Licence details unavailable";
    return licences
      .map((licence) => `${licence.typeAndRating || "Type/rating unavailable"} - ${licence.route || "Route unavailable"}`)
      .join("; ");
  }

  function locationText(entity) {
    return [entity.townCity, entity.county].filter(Boolean).join(", ") || "Location unavailable";
  }

  function renderCandidate(candidate, index) {
    const entity = candidate.entity || {};
    const item = createElement("article", "uksc-candidate");
    item.appendChild(createElement("h3", null, entity.officialName || `Candidate ${index + 1}`));
    item.appendChild(createElement("p", "uksc-meta", locationText(entity)));
    item.appendChild(createElement("p", "uksc-meta", licenceText(entity)));
    item.appendChild(createElement("p", "uksc-score", `Confidence: ${Math.round((candidate.score || 0) * 100)}%`));
    return item;
  }

  function removeCard() {
    const existing = document.getElementById(CARD_ID);
    if (existing) existing.remove();
  }

  function renderResult(result) {
    removeCard();

    const state = result.state || "error";
    const card = createElement("section", "uksc-card");
    card.id = CARD_ID;
    card.classList.add(`uksc-state-${state}`);
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-live", "polite");
    card.setAttribute("aria-label", "UK sponsorship check result");

    const header = createElement("div", "uksc-header");
    const title = createElement("div");
    title.appendChild(createElement("p", "uksc-eyebrow", "UK Sponsor Checker"));
    title.appendChild(createElement("h2", null, STATE_LABELS[state] || STATE_LABELS.error));

    const close = createElement("button", "uksc-close", "x");
    close.type = "button";
    close.setAttribute("aria-label", "Dismiss sponsor result");
    close.addEventListener("click", removeCard);

    header.appendChild(title);
    header.appendChild(close);
    card.appendChild(header);

    if (result.input) {
      card.appendChild(createElement("p", "uksc-selected", `Selected: ${result.input}`));
    }

    const candidates = result.candidates || [];
    if (candidates.length) {
      const list = createElement("div", "uksc-candidates");
      candidates.slice(0, 5).forEach((candidate, index) => {
        list.appendChild(renderCandidate(candidate, index));
      });
      card.appendChild(list);
    } else if (result.error) {
      card.appendChild(createElement("p", "uksc-body", result.error));
    }

    const metadata = result.metadata || {};
    const datasetDate = metadata.sourceDate || metadata.processedAt || "Dataset date unavailable";
    const source = createElement("p", "uksc-source", `Dataset: ${datasetDate} - ${metadata.sourceName || "UK Register of Licensed Sponsors"}`);
    card.appendChild(source);

    const link = createElement("a", "uksc-link", "Open official GOV.UK source");
    link.href = result.officialSourceUrl || "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers";
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    card.appendChild(link);

    card.appendChild(createElement("p", "uksc-disclaimer", DISCLAIMER));
    document.documentElement.appendChild(card);
    close.focus();
  }

  if (!window.ukSponsorCheckerContentLoaded) {
    window.ukSponsorCheckerContentLoaded = true;
    chrome.runtime.onMessage.addListener((message) => {
      if (message && message.type === "UK_SPONSOR_CHECK_RESULT") {
        renderResult(message.result || { state: "error", candidates: [] });
      }
    });
  }
})();
