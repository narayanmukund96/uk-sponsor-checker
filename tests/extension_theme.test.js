const assert = require("assert");
const fs = require("fs");

const css = fs.readFileSync("extension/content.css", "utf8");
const js = fs.readFileSync("extension/content.js", "utf8");

for (const state of ["exact", "probable", "ambiguous", "not_found", "error"]) {
  assert(css.includes(`uksc-state-${state}`), `missing CSS state ${state}`);
}

assert(js.includes("card.classList.add(`uksc-state-${state}`)"));
console.log("extension theme tests passed");
