from __future__ import annotations

import re
import unicodedata


LEGAL_SUFFIXES = {
    "limited",
    "ltd",
    "plc",
    "llp",
    "incorporated",
    "inc",
    "company",
    "co",
}

TRADING_MARKER_PATTERNS = [
    re.compile(r"\bt\s*/\s*a\b", re.IGNORECASE),
    re.compile(r"\bta\b", re.IGNORECASE),
    re.compile(r"\btrading\s+as\b", re.IGNORECASE),
]


def clean_source_value(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", clean_source_value(value)).casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"['’`]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\band\b", "and", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_legal_suffix(normalized_name: str) -> str:
    tokens = normalized_name.split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def trading_aliases(official_name: str) -> list[str]:
    aliases: set[str] = set()
    for pattern in TRADING_MARKER_PATTERNS:
        parts = pattern.split(official_name, maxsplit=1)
        if len(parts) != 2:
            continue
        legal_part = strip_legal_suffix(normalize_text(parts[0]))
        trading_part = normalize_text(parts[1])
        combined = normalize_text(f"{legal_part} {trading_part}")
        for alias in (legal_part, trading_part, combined):
            if alias:
                aliases.add(alias)
    return sorted(aliases)


def name_forms(official_name: str) -> dict[str, object]:
    normalized_name = normalize_text(official_name)
    base_name = strip_legal_suffix(normalized_name)
    aliases = set(trading_aliases(official_name))
    if base_name and base_name != normalized_name:
        aliases.add(base_name)
    aliases.discard(normalized_name)
    return {
        "normalized_name": normalized_name,
        "base_name": base_name,
        "aliases": sorted(aliases),
    }
