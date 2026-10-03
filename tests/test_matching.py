import unittest

from matching.engine import SponsorMatcher


DATASET = {
    "metadata": {"dataVersion": "test-version"},
    "entities": [
        {
            "id": "one",
            "officialName": "Example Services Ltd",
            "normalizedName": "example services ltd",
            "baseName": "example services",
            "aliases": [],
            "townCity": "London",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "two",
            "officialName": "BRANOS OXFORD LTD T/A LILO",
            "normalizedName": "branos oxford ltd t a lilo",
            "baseName": "branos oxford ltd t a lilo",
            "aliases": ["lilo", "branos oxford"],
            "townCity": "Oxford",
            "county": "Oxfordshire",
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "three",
            "officialName": "Acme Ltd",
            "normalizedName": "acme ltd",
            "baseName": "acme",
            "aliases": [],
            "townCity": "Leeds",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "four",
            "officialName": "Acme LLP",
            "normalizedName": "acme llp",
            "baseName": "acme",
            "aliases": [],
            "townCity": "Bristol",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "five",
            "officialName": "Creatio Britain Ltd",
            "normalizedName": "creatio britain ltd",
            "baseName": "creatio britain",
            "aliases": ["creatio britain"],
            "townCity": "London",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "six",
            "officialName": '"K" Line Energy Shipping (UK) Limited',
            "normalizedName": "k line energy shipping uk limited",
            "baseName": "k line energy shipping uk",
            "aliases": ["k line energy shipping uk"],
            "townCity": "London",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "seven",
            "officialName": "Energy Shipping Services Ltd",
            "normalizedName": "energy shipping services ltd",
            "baseName": "energy shipping services",
            "aliases": [],
            "townCity": "Liverpool",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "eight",
            "officialName": "Tether Operations Limited",
            "normalizedName": "tether operations limited",
            "baseName": "tether operations",
            "aliases": [],
            "townCity": "London",
            "county": None,
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
        {
            "id": "nine",
            "officialName": "Microsoft Limited",
            "normalizedName": "microsoft limited",
            "baseName": "microsoft",
            "aliases": ["microsoft"],
            "townCity": "Reading",
            "county": "Berkshire",
            "licences": [{"typeAndRating": "Worker (A rating)", "route": "Skilled Worker"}],
        },
    ],
}


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.matcher = SponsorMatcher(DATASET)

    def test_exact_official_match(self):
        result = self.matcher.match("Example Services Ltd")
        self.assertEqual(result["state"], "exact")
        self.assertEqual(result["candidates"][0]["sponsorId"], "one")

    def test_alias_match(self):
        result = self.matcher.match("Lilo")
        self.assertEqual(result["state"], "exact")
        self.assertEqual(result["candidates"][0]["sponsorId"], "two")

    def test_suffix_stripped_collision_is_ambiguous(self):
        result = self.matcher.match("Acme")
        self.assertEqual(result["state"], "ambiguous")
        self.assertEqual({item["sponsorId"] for item in result["candidates"]}, {"three", "four"})

    def test_single_brand_token_returns_probable(self):
        result = self.matcher.match("Creatio")
        self.assertEqual(result["state"], "probable")
        self.assertEqual(result["candidates"][0]["sponsorId"], "five")

    def test_ordered_partial_tokens_return_probable(self):
        result = self.matcher.match("K Line Energy")
        self.assertEqual(result["state"], "probable")
        self.assertEqual(result["candidates"][0]["sponsorId"], "six")

    def test_competing_partial_tokens_return_ambiguous(self):
        result = self.matcher.match("Energy Shipping")
        self.assertEqual(result["state"], "ambiguous")
        self.assertEqual({item["sponsorId"] for item in result["candidates"]}, {"six", "seven"})

    def test_domain_label_returns_probable_brand_match(self):
        result = self.matcher.match("tether.io")
        self.assertEqual(result["state"], "probable")
        self.assertEqual(result["candidates"][0]["sponsorId"], "eight")
        self.assertEqual(result["candidates"][0]["reasons"], ["domain_label", "single_brand_token"])

    def test_subdomain_url_uses_registrable_domain_label(self):
        result = self.matcher.match("https://jobs.microsoft.com/careers")
        self.assertEqual(result["state"], "exact")
        self.assertEqual(result["candidates"][0]["sponsorId"], "nine")

    def test_not_found_for_weak_match(self):
        result = self.matcher.match("Definitely Not A Sponsor")
        self.assertEqual(result["state"], "not_found")

    def test_invalid_input_returns_error(self):
        self.assertEqual(self.matcher.match("  ")["state"], "error")
        self.assertEqual(self.matcher.match("x" * 201)["state"], "error")


if __name__ == "__main__":
    unittest.main()
