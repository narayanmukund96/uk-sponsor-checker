from __future__ import annotations

import csv
from pathlib import Path

from .models import SourceRow, ValidationReport
from .normalize import clean_source_value
from .schema import REQUIRED_COLUMNS


def read_source_csv(path: Path) -> tuple[list[SourceRow], ValidationReport]:
    report = ValidationReport(accepted=True)
    if path.suffix.lower() != ".csv":
        report.add_error("Input file must be a CSV file.")
        return [], report

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
            if missing:
                report.add_error(f"Missing required columns: {', '.join(missing)}")
                return [], report

            unexpected = [column for column in fieldnames if column not in REQUIRED_COLUMNS]
            if unexpected:
                report.info.append(f"Unexpected columns preserved only in source file: {', '.join(unexpected)}")

            rows = []
            blank_town_count = 0
            blank_county_count = 0
            for line_number, raw in enumerate(reader, start=2):
                row = SourceRow(
                    organisation_name=clean_source_value(raw.get("Organisation Name")),
                    town_city=clean_source_value(raw.get("Town/City")),
                    county=clean_source_value(raw.get("County")),
                    type_and_rating=clean_source_value(raw.get("Type & Rating")),
                    route=clean_source_value(raw.get("Route")),
                )
                if not row.organisation_name:
                    report.add_error(f"Line {line_number}: Organisation Name is required.")
                if not row.town_city:
                    blank_town_count += 1
                if not row.county:
                    blank_county_count += 1
                rows.append(row)
            if blank_town_count:
                report.warnings.append(f"Town/City is blank for {blank_town_count} row(s).")
            if blank_county_count:
                report.warnings.append(f"County is blank for {blank_county_count} row(s).")
    except UnicodeDecodeError:
        report.add_error("Input file could not be decoded as UTF-8.")
        return [], report

    report.raw_row_count = len(rows)
    return rows, report


def validate_record_count(
    report: ValidationReport,
    current_count: int,
    *,
    min_row_count: int,
    previous_count: int | None = None,
    tolerance: float = 0.35,
) -> None:
    if current_count < min_row_count:
        report.add_error(f"Row count {current_count} is below minimum expected count {min_row_count}.")
    if previous_count is not None and previous_count > 0:
        change_ratio = abs(current_count - previous_count) / previous_count
        if change_ratio > tolerance:
            report.add_error(
                f"Row count changed by {change_ratio:.1%}, exceeding tolerance {tolerance:.1%}."
            )
