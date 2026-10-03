import unittest

from ingestion.normalize import name_forms, normalize_text, strip_legal_suffix


class NormalizationTests(unittest.TestCase):
    def test_normalizes_case_punctuation_ampersand_and_whitespace(self):
        self.assertEqual(normalize_text("  A&B--Services, LTD  "), "a and b services ltd")

    def test_strips_legal_suffix_only_from_base_name(self):
        self.assertEqual(strip_legal_suffix("example services limited"), "example services")

    def test_generates_trading_aliases_without_losing_official_name(self):
        forms = name_forms("BRANOS OXFORD LTD T/A LILO")
        self.assertEqual(forms["normalized_name"], "branos oxford ltd t a lilo")
        self.assertIn("lilo", forms["aliases"])
        self.assertIn("branos oxford", forms["aliases"])


if __name__ == "__main__":
    unittest.main()
