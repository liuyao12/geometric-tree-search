import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const document = readFileSync(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const styles = readFileSync(new URL("../apps/iqc-growth-live/style.css", import.meta.url), "utf8");
const readme = readFileSync(new URL("../apps/iqc-growth-live/README.md", import.meta.url), "utf8");
const benchmark = readFileSync(new URL("../docs/projects/materials-recursive-gcts-benchmark.md", import.meta.url), "utf8");
const atlas = readFileSync(new URL("../apps/iqc-growth-live/evidence-atlas.js", import.meta.url), "utf8");
const library = readFileSync(new URL("../apps/iqc-growth-live/public-powder-profile-library.mjs", import.meta.url), "utf8");
const libraryData = JSON.parse(readFileSync(new URL("../apps/iqc-growth-live/data/rruff-powder-profiles-v1.json", import.meta.url), "utf8"));

assert.match(app, /experimental-scattering-validation\.mjs\?v=20260901-418/);
assert.match(app, /public-powder-profile-library\.mjs\?v=20260901-418/);
assert.match(app, /experimentalPowderProfileValidation/);
assert.match(app, /candidateSetChanged: false/);
assert.match(app, /runExperimentalScatteringDemonstrator/);
assert.match(document, /Independent powder-profile validation/);
assert.match(document, /download pdCIF request/);
assert.match(document, /run instrument demonstrator/);
assert.match(document, /browse public RRUFF profiles/);
assert.match(document, /chemistry alone never establishes phase identity/);
assert.match(styles, /experimental-scattering-card/);
assert.match(styles, /public-powder-profile-panel/);
assert.match(styles, /profile-residual/);
assert.match(styles, /profile-uncertainty/);
assert.match(readme, /Build 417/);
assert.match(readme, /demonstratorOnly/);
assert.match(benchmark, /Independent powder-profile validation boundary/);
assert.match(atlas, /Experiment-facing powder validation/);
assert.match(library, /sameMaterialClaimAllowed/);
assert.match(library, /select the constant-Z electron-count X-ray approximation/);
assert.equal(libraryData.schema, "gcts-rruff-powder-profile-library-v1");
assert.equal(libraryData.profileCount, 15);
assert.equal(libraryData.profiles.filter(profile => profile.phase === "Halite").length, 3);
assert.equal(new Set(libraryData.profiles.map(profile => profile.rruffId)).size, 15);

console.log("experimental scattering portal contract: all tests passed");
