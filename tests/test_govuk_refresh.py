import unittest

from scripts.refresh_from_govuk import extract_csv_url, source_date_from_page


class GovukRefreshTests(unittest.TestCase):
    def test_extracts_csv_attachment_url(self):
        html = """
        <html><body>
          <a href="/government/uploads/system/uploads/attachment_data/file/123/register.csv">Download CSV</a>
        </body></html>
        """
        self.assertEqual(
            extract_csv_url("https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers", html),
            "https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/123/register.csv",
        )

    def test_extracts_last_updated_date(self):
        html = """
        <dt>Last updated:</dt>
        <dd class="gem-c-metadata__definition">25 August 2026</dd>
        """
        self.assertEqual(source_date_from_page(html), "2026-08-25")


if __name__ == "__main__":
    unittest.main()
