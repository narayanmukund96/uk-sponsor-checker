from __future__ import annotations

import hashlib

from .models import SourceRow
from .normalize import name_forms, normalize_text


def entity_id(official_name: str, town_city: str, county: str) -> str:
    raw = "\u241f".join([official_name, town_city, county])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def aggregate_rows(rows: list[SourceRow]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    licence_sets: dict[tuple[str, str, str], set[tuple[str, str]]] = {}

    for row in rows:
        key = (row.organisation_name, row.town_city, row.county)
        if key not in grouped:
            forms = name_forms(row.organisation_name)
            grouped[key] = {
                "id": entity_id(*key),
                "officialName": row.organisation_name,
                "normalizedName": forms["normalized_name"],
                "baseName": forms["base_name"],
                "aliases": forms["aliases"],
                "townCity": row.town_city or None,
                "normalizedTownCity": normalize_text(row.town_city) or None,
                "county": row.county or None,
                "normalizedCounty": normalize_text(row.county) or None,
                "licences": [],
            }
            licence_sets[key] = set()

        licence = (row.type_and_rating, row.route)
        if licence not in licence_sets[key]:
            licence_sets[key].add(licence)
            grouped[key]["licences"].append(
                {"typeAndRating": row.type_and_rating, "route": row.route}
            )

    entities = list(grouped.values())
    for entity in entities:
        entity["licences"] = sorted(
            entity["licences"],
            key=lambda item: (item["typeAndRating"], item["route"]),
        )
    return sorted(entities, key=lambda item: (item["officialName"], item.get("townCity") or "", item.get("county") or ""))
