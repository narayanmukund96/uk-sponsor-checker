import csv
import json
import tempfile
import unittest
from pathlib import Path

from ingestion.aggregate import aggregate_rows
from ingestion.publish import build_dataset
from ingestion.validate import read_source_csv, validate_record_count


HEADER = ["Organisation Name", "Town/City", "County", "Type & Rating", "Route"]


class IngestionTests(unittest.TestCase):
    def write_csv(self, rows, header=HEADER):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "register.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)
        self.addCleanup(directory.cleanup)
        return path

    def test_valid_csv_is_read_and_blank_county_warns(self):
        path = self.write_csv([["Example Ltd", "London", "", "Worker (A rating)", "Skilled Worker"]])
        rows, report = read_source_csv(path)
        validate_record_count(report, len(rows), min_row_count=1)
        self.assertTrue(report.accepted)
        self.assertEqual(len(rows), 1)
        self.assertIn("County is blank for 1 row(s).", report.warnings)

    def test_missing_required_column_is_rejected(self):
        path = self.write_csv([["Example Ltd"]], header=["Organisation Name"])
        _rows, report = read_source_csv(path)
        self.assertFalse(report.accepted)
        self.assertIn("Missing required columns", report.errors[0])

    def test_aggregation_preserves_distinct_routes(self):
        rows, report = read_source_csv(
            self.write_csv(
                [
                    ["Example Ltd", "London", "", "Worker (A rating)", "Skilled Worker"],
                    ["Example Ltd", "London", "", "Worker (A rating)", "Scale-up"],
                ]
            )
        )
        self.assertTrue(report.accepted)
        entities = aggregate_rows(rows)
        self.assertEqual(len(entities), 1)
        self.assertEqual(len(entities[0]["licences"]), 2)

    def test_dataset_metadata_contains_checksum_and_counts(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-07-21.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            writer.writerow(["Example Ltd", "London", "", "Worker (A rating)", "Skilled Worker"])
        rows, _report = read_source_csv(path)
        dataset = build_dataset(path, rows)
        self.assertEqual(dataset["metadata"]["rawRowCount"], 1)
        self.assertEqual(dataset["metadata"]["entityCount"], 1)
        self.assertEqual(dataset["metadata"]["sourceDate"], "2026-07-21")
        self.assertEqual(len(dataset["metadata"]["sha256"]), 64)
        json.dumps(dataset)

    def test_dataset_metadata_reads_short_download_date(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "Work visa - 250826.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            writer.writerow(["Example Ltd", "London", "", "Worker (A rating)", "Skilled Worker"])
        rows, _report = read_source_csv(path)
        dataset = build_dataset(path, rows)
        self.assertEqual(dataset["metadata"]["sourceDate"], "2026-08-25")

    def test_dataset_metadata_reads_short_date_after_underscore(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "UK Visa_sponsor_list_031026.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            writer.writerow(["Example Ltd", "London", "", "Worker (A rating)", "Skilled Worker"])
        rows, _report = read_source_csv(path)
        dataset = build_dataset(path, rows)
        self.assertEqual(dataset["metadata"]["sourceDate"], "2026-10-03")


if __name__ == "__main__":
    unittest.main()
