from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.cli import previous_raw_count
from ingestion.publish import build_dataset, report_payload, write_json
from ingestion.validate import read_source_csv, validate_record_count


DEFAULT_PAGE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.links.append(value)


def read_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "uk-sponsor-checker-updater/0.1"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def extract_csv_url(page_url: str, html: str) -> str:
    parser = LinkParser()
    parser.feed(html)
    candidates = [urljoin(page_url, link) for link in parser.links]

    for candidate in candidates:
        parsed = urlparse(candidate)
        if parsed.path.lower().endswith(".csv"):
            return candidate

    for candidate in candidates:
        if "attachment_data" in candidate and "register" in candidate.lower():
            return candidate

    raise ValueError("Could not find a CSV attachment link on the GOV.UK register page.")


def source_date_from_page(html: str) -> str:
    match = re.search(r"Last updated:\s*</dt>\s*<dd[^>]*>\s*([0-9]{1,2})\s+([A-Za-z]+)\s+(20[0-9]{2})", html)
    if not match:
        return datetime.now(timezone.utc).date().isoformat()
    day, month_name, year = match.groups()
    month = datetime.strptime(month_name[:3], "%b").month
    return f"{year}-{month:02d}-{int(day):02d}"


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def promote(versioned_dataset: Path, canonical_dataset: Path, extension_dataset: Path) -> None:
    canonical_dataset.parent.mkdir(parents=True, exist_ok=True)
    extension_dataset.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(versioned_dataset, canonical_dataset)
    shutil.copy2(versioned_dataset, extension_dataset)


def run(args: argparse.Namespace) -> int:
    page_html = read_url(args.page_url).decode("utf-8", errors="replace")
    csv_url = extract_csv_url(args.page_url, page_html)
    source_date = args.source_date or source_date_from_page(page_html)

    raw_path = Path(args.raw_dir) / f"sponsor-register-{source_date}.csv"
    versioned_dataset = Path(args.processed_dir) / f"sponsors-{source_date}.json"
    report_path = Path(args.report_dir) / f"validation-report-{source_date}.json"

    if args.dry_run:
        print(json.dumps({"sourceDate": source_date, "csvUrl": csv_url, "rawPath": str(raw_path)}, indent=2))
        return 0

    write_bytes(raw_path, read_url(csv_url))
    rows, report = read_source_csv(raw_path)
    validate_record_count(
        report,
        len(rows),
        min_row_count=args.min_row_count,
        previous_count=previous_raw_count(Path(args.previous)) if args.previous else None,
        tolerance=args.tolerance,
    )
    write_json(report_path, report_payload(report))
    if not report.accepted:
        print("Downloaded source failed validation; existing extension dataset was left unchanged.", file=sys.stderr)
        return 1

    dataset = build_dataset(raw_path, rows)
    dataset["metadata"]["sourceDate"] = source_date
    write_json(versioned_dataset, dataset)
    promote(versioned_dataset, Path(args.canonical), Path(args.extension_data))
    print(json.dumps(dataset["metadata"], indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download, validate and publish the current GOV.UK sponsor register.")
    parser.add_argument("--page-url", default=DEFAULT_PAGE_URL)
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--report-dir", default="data/reports")
    parser.add_argument("--canonical", default="data/processed/sponsors.json")
    parser.add_argument("--extension-data", default="extension/data/sponsors.json")
    parser.add_argument("--previous", default="data/processed/sponsors.json")
    parser.add_argument("--min-row-count", type=int, default=100000)
    parser.add_argument("--tolerance", type=float, default=0.35)
    parser.add_argument("--source-date")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
