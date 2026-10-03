(function (root) {
  "use strict";

  const MAX_INPUT_LENGTH = 200;
  const FUZZY_MIN_SCORE = 0.93;
  const AMBIGUITY_MARGIN = 0.04;
  const PARTIAL_MIN_SCORE = 0.84;
  const PARTIAL_CLEAR_MARGIN = 0.08;
  const MAX_CANDIDATES = 5;
  const COMMON_TOKENS = new Set([
    "and",
    "the",
    "of",
    "uk",
    "limited",
    "ltd",
    "plc",
    "llp",
    "inc",
    "co",
    "company",
    "group",
    "services"
  ]);

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFKC")
      .trim()
      .toLowerCase()
      .replace(/&/g, " and ")
      .replace(/[''`]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function domainLabel(value) {
    const text = String(value || "").trim().toLowerCase();
    if (!text || !/[.@]/.test(text)) return "";

    let host = text;
    const emailMatch = host.match(/[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})/i);
    if (emailMatch) {
      host = emailMatch[1];
    } else {
      host = host.replace(/^[a-z][a-z0-9+.-]*:\/\//i, "");
      host = host.split(/[/?#\s]/)[0];
    }

    host = host.replace(/^www\./, "").replace(/:\d+$/, "");
    if (!/^[a-z0-9.-]+\.[a-z]{2,}$/.test(host)) return "";

    const labels = host.split(".").filter(Boolean);
    if (labels.length < 2) return "";
    const secondLevelSuffixes = new Set(["co", "com", "org", "net", "ac", "gov", "ltd", "plc"]);
    const registrableIndex =
      labels.length >= 3 && labels[labels.length - 1].length === 2 && secondLevelSuffixes.has(labels[labels.length - 2])
        ? labels.length - 3
        : labels.length - 2;
    return labels[registrableIndex] || "";
  }

  function searchForms(value) {
    const normalized = normalizeText(value);
    const forms = [{ value: normalized, reasonPrefix: "" }];
    const label = normalizeText(domainLabel(value));
    if (label && label !== normalized) {
      forms.push({ value: label, reasonPrefix: "domain_label" });
    }
    return forms;
  }

  function distinctiveTokens(value) {
    return normalizeText(value)
      .split(" ")
      .filter((token) => token.length > 1 && !COMMON_TOKENS.has(token));
  }

  function addToIndex(index, key, entityId) {
    if (!key) return;
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(entityId);
  }

  function levenshteinDistance(a, b) {
    if (a === b) return 0;
    if (!a.length) return b.length;
    if (!b.length) return a.length;

    const previous = new Array(b.length + 1);
    const current = new Array(b.length + 1);
    for (let j = 0; j <= b.length; j += 1) previous[j] = j;

    for (let i = 1; i <= a.length; i += 1) {
      current[0] = i;
      for (let j = 1; j <= b.length; j += 1) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        current[j] = Math.min(
          current[j - 1] + 1,
          previous[j] + 1,
          previous[j - 1] + cost
        );
      }
      for (let j = 0; j <= b.length; j += 1) previous[j] = current[j];
    }
    return previous[b.length];
  }

  function similarity(a, b) {
    const longest = Math.max(a.length, b.length);
    if (!longest) return 1;
    return 1 - levenshteinDistance(a, b) / longest;
  }

  function candidate(entity, score, reason) {
    return {
      sponsorId: entity.id,
      score,
      reasons: [reason],
      entity
    };
  }

  function withReasonPrefix(result, prefix) {
    if (!result || !prefix) return result;
    return {
      ...result,
      candidates: result.candidates.map((item) => ({
        ...item,
        reasons: [prefix, ...item.reasons]
      }))
    };
  }

  function publicCandidate(match) {
    return {
      sponsorId: match.sponsorId,
      score: match.score,
      reasons: match.reasons,
      entity: match.entity
    };
  }

  function isOrderedSubsequence(needles, haystack) {
    let position = 0;
    for (const token of haystack) {
      if (token === needles[position]) position += 1;
      if (position === needles.length) return true;
    }
    return false;
  }

  function startsWithTokens(haystack, needles) {
    if (needles.length > haystack.length) return false;
    return needles.every((token, index) => haystack[index] === token);
  }

  function partialTokenScore(inputTokens, formTokens) {
    if (!inputTokens.length || !formTokens.length) return 0;
    if (!inputTokens.every((token) => formTokens.includes(token))) return 0;
    if (startsWithTokens(formTokens, inputTokens)) return 0.94;
    if (isOrderedSubsequence(inputTokens, formTokens) && inputTokens[0] === formTokens[0]) return 0.9;
    if (isOrderedSubsequence(inputTokens, formTokens)) return 0.86;
    return 0.78;
  }

  class SponsorMatcher {
    constructor(dataset) {
      if (!dataset || !Array.isArray(dataset.entities)) {
        throw new Error("Sponsor dataset is malformed.");
      }
      this.metadata = dataset.metadata || {};
      this.entitiesById = new Map();
      this.officialIndex = new Map();
      this.aliasIndex = new Map();
      this.baseIndex = new Map();
      this.tokenIndex = new Map();

      for (const entity of dataset.entities) {
        this.entitiesById.set(entity.id, entity);
        addToIndex(this.officialIndex, entity.normalizedName, entity.id);
        addToIndex(this.baseIndex, entity.baseName, entity.id);
        for (const alias of entity.aliases || []) {
          addToIndex(this.aliasIndex, alias, entity.id);
        }
        const searchForms = [entity.normalizedName, entity.baseName, ...(entity.aliases || [])];
        for (const form of searchForms) {
          for (const token of distinctiveTokens(form)) {
            addToIndex(this.tokenIndex, token, entity.id);
          }
        }
      }
    }

    match(input) {
      const original = String(input || "");
      const normalized = normalizeText(original);
      const baseResult = {
        state: "error",
        input: original,
        normalizedInput: normalized,
        candidates: [],
        datasetVersion: this.metadata.dataVersion || null,
        metadata: this.metadata
      };

      if (!normalized || original.length > MAX_INPUT_LENGTH) {
        return {
          ...baseResult,
          error: "Invalid selected text."
        };
      }

      for (const form of searchForms(original)) {
        if (!form.value) continue;
        const exactResult = this.matchIndex(this.officialIndex, form.value, "official_normalized_exact");
        if (exactResult) return { ...baseResult, ...withReasonPrefix(exactResult, form.reasonPrefix) };

        const aliasResult = this.matchIndex(this.aliasIndex, form.value, "approved_alias_exact");
        if (aliasResult) return { ...baseResult, ...withReasonPrefix(aliasResult, form.reasonPrefix) };

        const baseNameResult = this.matchIndex(this.baseIndex, form.value, "base_name_exact");
        if (baseNameResult) return { ...baseResult, ...withReasonPrefix(baseNameResult, form.reasonPrefix) };

        const tokenResult = this.matchSingleToken(form.value);
        if (tokenResult) return { ...baseResult, ...withReasonPrefix(tokenResult, form.reasonPrefix) };

        const partialResult = this.matchPartialTokens(form.value);
        if (partialResult) return { ...baseResult, ...withReasonPrefix(partialResult, form.reasonPrefix) };
      }

      const fuzzy = this.fuzzyCandidates(normalized);
      if (!fuzzy.length) {
        return { ...baseResult, state: "not_found" };
      }
      if (fuzzy.length > 1 && fuzzy[0].score - fuzzy[1].score <= AMBIGUITY_MARGIN) {
        return {
          ...baseResult,
          state: "ambiguous",
          candidates: fuzzy.map(publicCandidate)
        };
      }
      return {
        ...baseResult,
        state: "probable",
        candidates: [publicCandidate(fuzzy[0])]
      };
    }

    matchIndex(index, key, reason) {
      const ids = index.get(key) || [];
      if (!ids.length) return null;
      const matches = ids.map((id) => candidate(this.entitiesById.get(id), 1, reason));
      return {
        state: matches.length === 1 ? "exact" : "ambiguous",
        candidates: matches.map(publicCandidate)
      };
    }

    matchSingleToken(normalized) {
      const tokens = distinctiveTokens(normalized);
      if (tokens.length !== 1 || tokens[0] !== normalized || normalized.length < 4) {
        return null;
      }
      const ids = Array.from(new Set(this.tokenIndex.get(normalized) || []));
      if (!ids.length) return null;
      const matches = ids
        .map((id) => this.entitiesById.get(id))
        .filter((entity) => {
          const firstTokens = [entity.normalizedName, entity.baseName, ...(entity.aliases || [])]
            .filter(Boolean)
            .map((form) => distinctiveTokens(form)[0]);
          return firstTokens.includes(normalized);
        })
        .map((entity) => candidate(entity, 0.9, "single_brand_token"));
      if (!matches.length) return null;
      return {
        state: matches.length === 1 ? "probable" : "ambiguous",
        candidates: matches.slice(0, MAX_CANDIDATES).map(publicCandidate)
      };
    }

    matchPartialTokens(normalized) {
      const inputTokens = distinctiveTokens(normalized);
      if (inputTokens.length < 2) return null;

      const ids = new Set();
      for (const token of inputTokens) {
        for (const id of this.tokenIndex.get(token) || []) {
          ids.add(id);
        }
      }

      const matches = [];
      for (const id of ids) {
        const entity = this.entitiesById.get(id);
        const forms = [entity.normalizedName, entity.baseName, ...(entity.aliases || [])].filter(Boolean);
        let bestScore = 0;
        for (const form of forms) {
          bestScore = Math.max(bestScore, partialTokenScore(inputTokens, distinctiveTokens(form)));
        }
        if (bestScore >= PARTIAL_MIN_SCORE) {
          matches.push(candidate(entity, Number(bestScore.toFixed(4)), "ordered_partial_tokens"));
        }
      }

      const ranked = matches.sort((a, b) => b.score - a.score).slice(0, MAX_CANDIDATES);
      if (!ranked.length) return null;
      if (ranked.length > 1 && ranked[0].score - ranked[1].score <= PARTIAL_CLEAR_MARGIN) {
        return {
          state: "ambiguous",
          candidates: ranked.map(publicCandidate)
        };
      }
      return {
        state: "probable",
        candidates: [publicCandidate(ranked[0])]
      };
    }

    fuzzyCandidates(normalized) {
      const ids = new Set();
      for (const token of distinctiveTokens(normalized)) {
        for (const id of this.tokenIndex.get(token) || []) {
          ids.add(id);
        }
      }
      const matches = [];
      for (const id of ids) {
        const entity = this.entitiesById.get(id);
        const forms = [entity.normalizedName, entity.baseName, ...(entity.aliases || [])].filter(Boolean);
        const score = Math.max(...forms.map((form) => similarity(normalized, form)));
        if (score >= FUZZY_MIN_SCORE) {
          matches.push(candidate(entity, Number(score.toFixed(4)), "conservative_fuzzy"));
        }
      }
      return matches.sort((a, b) => b.score - a.score).slice(0, MAX_CANDIDATES);
    }
  }

  root.UkSponsorCheckerMatcher = {
    SponsorMatcher,
    normalizeText,
    domainLabel
  };

  if (typeof module !== "undefined") {
    module.exports = root.UkSponsorCheckerMatcher;
  }
})(typeof globalThis !== "undefined" ? globalThis : window);
