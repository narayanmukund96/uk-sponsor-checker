from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .aggregate import aggregate_rows
from .models import SourceRow, ValidationReport
from .schema import SCHEMA_VERSION, SOURCE_NAME


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_date_from_filename(path: Path) -> str | None:
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", path.name)
    if match:
        return "-".join(match.groups())
    short_match = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", path.stem)
    if short_match:
        day, month, year = short_match.groups()
        return f"20{year}-{month}-{day}"
    return None


def build_dataset(source_path: Path, rows: list[SourceRow]) -> dict[str, object]:
    entities = aggregate_rows(rows)
    processed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    checksum = sha256_file(source_path)
    metadata = {
        "sourceName": SOURCE_NAME,
        "sourceFileName": source_path.name,
        "processedAt": processed_at,
        "sourceDate": source_date_from_filename(source_path),
        "rawRowCount": len(rows),
        "entityCount": len(entities),
        "sha256": checksum,
        "schemaVersion": SCHEMA_VERSION,
        "dataVersion": checksum[:12],
    }
    return {"metadata": metadata, "entities": entities}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def report_payload(report: ValidationReport) -> dict[str, object]:
    return {
        "accepted": report.accepted,
        "errors": report.errors,
        "warnings": report.warnings,
        "info": report.info,
        "rawRowCount": report.raw_row_count,
    }
