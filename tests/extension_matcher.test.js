const assert = require("assert");
const { SponsorMatcher } = require("../extension/matcher.js");

const dataset = {
  metadata: {
    dataVersion: "test-version",
    sourceDate: "2026-07-21",
    sourceName: "UK Register of Licensed Sponsors"
  },
  entities: [
    {
      id: "one",
      officialName: "Example Services Ltd",
      normalizedName: "example services ltd",
      baseName: "example services",
      aliases: [],
      townCity: "London",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "two",
      officialName: "BRANOS OXFORD LTD T/A LILO",
      normalizedName: "branos oxford ltd t a lilo",
      baseName: "branos oxford ltd t a lilo",
      aliases: ["lilo", "branos oxford"],
      townCity: "Oxford",
      county: "Oxfordshire",
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "three",
      officialName: "Acme Ltd",
      normalizedName: "acme ltd",
      baseName: "acme",
      aliases: [],
      townCity: "Leeds",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "four",
      officialName: "Acme LLP",
      normalizedName: "acme llp",
      baseName: "acme",
      aliases: [],
      townCity: "Bristol",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "five",
      officialName: "Creatio Britain Ltd",
      normalizedName: "creatio britain ltd",
      baseName: "creatio britain",
      aliases: ["creatio britain"],
      townCity: "London",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "six",
      officialName: "\"K\" Line Energy Shipping (UK) Limited",
      normalizedName: "k line energy shipping uk limited",
      baseName: "k line energy shipping uk",
      aliases: ["k line energy shipping uk"],
      townCity: "London",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "seven",
      officialName: "Energy Shipping Services Ltd",
      normalizedName: "energy shipping services ltd",
      baseName: "energy shipping services",
      aliases: [],
      townCity: "Liverpool",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "eight",
      officialName: "Tether Operations Limited",
      normalizedName: "tether operations limited",
      baseName: "tether operations",
      aliases: [],
      townCity: "London",
      county: null,
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    },
    {
      id: "nine",
      officialName: "Microsoft Limited",
      normalizedName: "microsoft limited",
      baseName: "microsoft",
      aliases: ["microsoft"],
      townCity: "Reading",
      county: "Berkshire",
      licences: [{ typeAndRating: "Worker (A rating)", route: "Skilled Worker" }]
    }
  ]
};

const matcher = new SponsorMatcher(dataset);

assert.strictEqual(matcher.match("Example Services Ltd").state, "exact");
assert.strictEqual(matcher.match("Lilo").candidates[0].sponsorId, "two");
assert.strictEqual(matcher.match("Acme").state, "ambiguous");
const creatio = matcher.match("Creatio");
assert.strictEqual(creatio.state, "probable");
assert.strictEqual(creatio.candidates[0].sponsorId, "five");
const kLine = matcher.match("K Line Energy");
assert.strictEqual(kLine.state, "probable");
assert.strictEqual(kLine.candidates[0].sponsorId, "six");
assert.strictEqual(matcher.match("Energy Shipping").state, "ambiguous");
const tetherDomain = matcher.match("tether.io");
assert.strictEqual(tetherDomain.state, "probable");
assert.strictEqual(tetherDomain.candidates[0].sponsorId, "eight");
assert.deepStrictEqual(tetherDomain.candidates[0].reasons, ["domain_label", "single_brand_token"]);
const microsoftDomain = matcher.match("https://jobs.microsoft.com/careers");
assert.strictEqual(microsoftDomain.state, "exact");
assert.strictEqual(microsoftDomain.candidates[0].sponsorId, "nine");
assert.strictEqual(matcher.match("Definitely Not A Sponsor").state, "not_found");
assert.strictEqual(matcher.match("  ").state, "error");
assert.strictEqual(matcher.match("x".repeat(201)).state, "error");

console.log("extension matcher tests passed");
