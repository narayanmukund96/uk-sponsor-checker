from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from ingestion.normalize import normalize_text


MAX_INPUT_LENGTH = 200
FUZZY_MIN_SCORE = 0.93
AMBIGUITY_MARGIN = 0.04
PARTIAL_MIN_SCORE = 0.84
PARTIAL_CLEAR_MARGIN = 0.08
COMMON_TOKENS = {
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
    "services",
}


def distinctive_tokens(value: str) -> list[str]:
    return [token for token in normalize_text(value).split() if len(token) > 1 and token not in COMMON_TOKENS]


def domain_label(value: str) -> str:
    text = str(value or "").strip().casefold()
    if not text or "." not in text and "@" not in text:
        return ""
    email_match = re.search(r"[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})", text)
    if email_match:
        host = email_match.group(1)
    else:
        host = re.sub(r"^[a-z][a-z0-9+.-]*://", "", text)
        host = re.split(r"[/?#\s]", host)[0]
    host = re.sub(r"^www\.", "", host)
    host = re.sub(r":\d+$", "", host)
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", host):
        return ""
    labels = [label for label in host.split(".") if label]
    if len(labels) < 2:
        return ""
    second_level_suffixes = {"co", "com", "org", "net", "ac", "gov", "ltd", "plc"}
    if len(labels) >= 3 and len(labels[-1]) == 2 and labels[-2] in second_level_suffixes:
        return labels[-3]
    return labels[-2]


def search_forms(value: str) -> list[tuple[str, str]]:
    normalized = normalize_text(value)
    forms = [(normalized, "")]
    label = normalize_text(domain_label(value))
    if label and label != normalized:
        forms.append((label, "domain_label"))
    return forms


def with_reason_prefix(candidates: list[Candidate], prefix: str) -> list[Candidate]:
    if not prefix:
        return candidates
    return [
        Candidate(candidate.sponsorId, candidate.score, [prefix, *candidate.reasons])
        for candidate in candidates
    ]


def is_ordered_subsequence(needles: list[str], haystack: list[str]) -> bool:
    position = 0
    for token in haystack:
        if token == needles[position]:
            position += 1
        if position == len(needles):
            return True
    return False


def starts_with_tokens(haystack: list[str], needles: list[str]) -> bool:
    return len(needles) <= len(haystack) and all(token == haystack[index] for index, token in enumerate(needles))


def partial_token_score(input_tokens: list[str], form_tokens: list[str]) -> float:
    if not input_tokens or not form_tokens:
        return 0.0
    if not all(token in form_tokens for token in input_tokens):
        return 0.0
    if starts_with_tokens(form_tokens, input_tokens):
        return 0.94
    if is_ordered_subsequence(input_tokens, form_tokens) and input_tokens[0] == form_tokens[0]:
        return 0.9
    if is_ordered_subsequence(input_tokens, form_tokens):
        return 0.86
    return 0.78


@dataclass(frozen=True)
class Candidate:
    sponsorId: str
    score: float
    reasons: list[str]


class SponsorMatcher:
    def __init__(self, dataset: dict[str, object]):
        self.dataset = dataset
        self.metadata = dataset.get("metadata", {})
        self.entities = dataset.get("entities", [])
        self.official_index = self._build_index("normalizedName")
        self.base_index = self._build_index("baseName")
        self.alias_index = self._build_alias_index()
        self.token_index = self._build_token_index()

    def match(self, value: str | None) -> dict[str, object]:
        original = "" if value is None else str(value)
        normalized = normalize_text(original)
        base_result = {
            "input": original,
            "normalizedInput": normalized,
            "datasetVersion": self.metadata.get("dataVersion"),
            "candidates": [],
        }

        if not normalized or len(original) > MAX_INPUT_LENGTH:
            return {**base_result, "state": "error", "error": "Invalid selected text."}

        for form, prefix in search_forms(original):
            for index, reason in (
                (self.official_index, "official_normalized_exact"),
                (self.alias_index, "approved_alias_exact"),
                (self.base_index, "base_name_exact"),
            ):
                candidates = with_reason_prefix(self._candidates_from_index(index, form, reason), prefix)
                if len(candidates) == 1:
                    return {**base_result, "state": "exact", "candidates": [candidates[0].__dict__]}
                if len(candidates) > 1:
                    return {**base_result, "state": "ambiguous", "candidates": [item.__dict__ for item in candidates]}

            token_candidates = with_reason_prefix(self._single_token_candidates(form), prefix)
            if len(token_candidates) == 1:
                return {**base_result, "state": "probable", "candidates": [token_candidates[0].__dict__]}
            if len(token_candidates) > 1:
                return {**base_result, "state": "ambiguous", "candidates": [item.__dict__ for item in token_candidates]}

            partial_candidates = with_reason_prefix(self._partial_token_candidates(form), prefix)
            if len(partial_candidates) == 1:
                return {**base_result, "state": "probable", "candidates": [partial_candidates[0].__dict__]}
            if len(partial_candidates) > 1:
                return {**base_result, "state": "ambiguous", "candidates": [item.__dict__ for item in partial_candidates]}

        fuzzy = self._fuzzy_candidates(normalized)
        if not fuzzy:
            return {**base_result, "state": "not_found"}
        if len(fuzzy) > 1 and fuzzy[0].score - fuzzy[1].score <= AMBIGUITY_MARGIN:
            return {**base_result, "state": "ambiguous", "candidates": [item.__dict__ for item in fuzzy]}
        return {**base_result, "state": "probable", "candidates": [fuzzy[0].__dict__]}

    def _build_index(self, key: str) -> dict[str, list[dict[str, object]]]:
        index: dict[str, list[dict[str, object]]] = {}
        for entity in self.entities:
            value = entity.get(key)
            if value:
                index.setdefault(str(value), []).append(entity)
        return index

    def _build_alias_index(self) -> dict[str, list[dict[str, object]]]:
        index: dict[str, list[dict[str, object]]] = {}
        for entity in self.entities:
            for alias in entity.get("aliases", []):
                index.setdefault(str(alias), []).append(entity)
        return index

    def _build_token_index(self) -> dict[str, list[dict[str, object]]]:
        index: dict[str, list[dict[str, object]]] = {}
        for entity in self.entities:
            forms = [entity.get("normalizedName"), entity.get("baseName"), *entity.get("aliases", [])]
            for form in forms:
                for token in distinctive_tokens(str(form)):
                    index.setdefault(token, []).append(entity)
        return index

    def _candidates_from_index(
        self,
        index: dict[str, list[dict[str, object]]],
        key: str,
        reason: str,
    ) -> list[Candidate]:
        return [
            Candidate(sponsorId=str(entity["id"]), score=1.0, reasons=[reason])
            for entity in index.get(key, [])
        ]

    def _single_token_candidates(self, normalized: str) -> list[Candidate]:
        tokens = distinctive_tokens(normalized)
        if len(tokens) != 1 or tokens[0] != normalized or len(normalized) < 4:
            return []
        unique_entities = {
            str(entity["id"]): entity
            for entity in self.token_index.get(normalized, [])
        }
        matches = []
        for entity in unique_entities.values():
            forms = [entity.get("normalizedName"), entity.get("baseName"), *entity.get("aliases", [])]
            first_tokens = [distinctive_tokens(str(form))[0] for form in forms if distinctive_tokens(str(form))]
            if normalized in first_tokens:
                matches.append(Candidate(str(entity["id"]), 0.9, ["single_brand_token"]))
        return matches[:5]

    def _partial_token_candidates(self, normalized: str) -> list[Candidate]:
        input_tokens = distinctive_tokens(normalized)
        if len(input_tokens) < 2:
            return []
        unique_entities = {}
        for token in input_tokens:
            for entity in self.token_index.get(token, []):
                unique_entities[str(entity["id"])] = entity
        matches = []
        for entity in unique_entities.values():
            forms = [entity.get("normalizedName"), entity.get("baseName"), *entity.get("aliases", [])]
            best_score = max(partial_token_score(input_tokens, distinctive_tokens(str(form))) for form in forms if form)
            if best_score >= PARTIAL_MIN_SCORE:
                matches.append(Candidate(str(entity["id"]), round(best_score, 4), ["ordered_partial_tokens"]))
        ranked = sorted(matches, key=lambda item: item.score, reverse=True)[:5]
        if len(ranked) > 1 and ranked[0].score - ranked[1].score <= PARTIAL_CLEAR_MARGIN:
            return ranked
        return ranked[:1]

    def _fuzzy_candidates(self, normalized: str) -> list[Candidate]:
        input_tokens = set(normalized.split())
        candidates: list[Candidate] = []
        for entity in self.entities:
            haystacks = [entity.get("normalizedName"), entity.get("baseName"), *entity.get("aliases", [])]
            token_sets = [set(str(item).split()) for item in haystacks if item]
            if input_tokens and not any(input_tokens & tokens for tokens in token_sets):
                continue
            score = max(SequenceMatcher(None, normalized, str(item)).ratio() for item in haystacks if item)
            if score >= FUZZY_MIN_SCORE:
                candidates.append(Candidate(str(entity["id"]), round(score, 4), ["conservative_fuzzy"]))
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:5]
