from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .publish import build_dataset, report_payload, write_json
from .validate import read_source_csv, validate_record_count


def previous_raw_count(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", payload)
    value = metadata.get("rawRowCount")
    return int(value) if value is not None else None


def run(args: argparse.Namespace) -> int:
    source_path = Path(args.input)
    rows, report = read_source_csv(source_path)
    validate_record_count(
        report,
        len(rows),
        min_row_count=args.min_row_count,
        previous_count=previous_raw_count(Path(args.previous)) if args.previous else None,
        tolerance=args.tolerance,
    )

    if args.report:
        write_json(Path(args.report), report_payload(report))

    if args.command == "validate":
        print(json.dumps(report_payload(report), indent=2, sort_keys=True))
        return 0 if report.accepted else 1

    if not report.accepted:
        print("Input rejected; processed dataset was not published.", file=sys.stderr)
        return 1

    dataset = build_dataset(source_path, rows)
    write_json(Path(args.output), dataset)
    print(json.dumps(dataset["metadata"], indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and transform the UK sponsor register CSV.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "update"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--input", required=True, help="Path to the official source CSV.")
        sub.add_argument("--report", help="Path for the human-readable validation report JSON.")
        sub.add_argument("--previous", help="Path to the previous accepted dataset or metadata JSON.")
        sub.add_argument("--min-row-count", type=int, default=100000)
        sub.add_argument("--tolerance", type=float, default=0.35)
        if command == "update":
            sub.add_argument("--output", required=True, help="Path for the processed sponsor dataset JSON.")
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
