import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const document = readFileSync(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const styles = readFileSync(new URL("../apps/iqc-growth-live/style.css", import.meta.url), "utf8");
const readme = readFileSync(new URL("../apps/iqc-growth-live/README.md", import.meta.url), "utf8");
const benchmark = readFileSync(new URL("../docs/projects/materials-recursive-gcts-benchmark.md", import.meta.url), "utf8");

assert.match(app, /critical-nucleus-grammar-admission\.mjs\?v=20260901-429/);
assert.match(app, /auditCriticalNucleusGrammarAdmission/);
assert.match(app, /initializeExternalCriticalNucleusSeed/);
assert.match(app, /candidateSetInspectedDuringAdmission: false/);
assert.match(document, /Frozen GCTS seed admission/);
assert.match(document, /Use as local GCTS seed/);
assert.match(document, /value="external-critical-nucleus" disabled/);
assert.match(styles, /critical-nucleus-grammar-admission/);
assert.match(readme, /Build 415/);
assert.match(benchmark, /Frozen-grammar admission of atomistic critical nuclei/);

console.log("critical nucleus grammar admission portal contract: all tests passed");
