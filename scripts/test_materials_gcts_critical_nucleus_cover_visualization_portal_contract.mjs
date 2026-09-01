import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const document = readFileSync(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const styles = readFileSync(new URL("../apps/iqc-growth-live/style.css", import.meta.url), "utf8");
const readme = readFileSync(new URL("../apps/iqc-growth-live/README.md", import.meta.url), "utf8");
const benchmark = readFileSync(new URL("../docs/projects/materials-recursive-gcts-benchmark.md", import.meta.url), "utf8");

assert.match(app, /critical-nucleus-cover-visualization\.mjs\?v=20260901-431/);
assert.match(app, /buildCriticalNucleusCoverVisualization/);
assert.match(app, /criticalNucleusViewMode !== "atoms"/);
assert.match(document, /Learned cluster cover/);
assert.match(document, /Admitted port graph/);
assert.match(styles, /critical-nucleus-residual-ring/);
assert.match(styles, /critical-nucleus-frontier-halo/);
assert.match(readme, /Build 416/);
assert.match(benchmark, /Interactive critical-nucleus cover and port evidence/);

console.log("critical nucleus cover visualization portal contract: all tests passed");
