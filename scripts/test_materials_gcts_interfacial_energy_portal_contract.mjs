import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const readme = readFileSync(new URL("../apps/iqc-growth-live/README.md", import.meta.url), "utf8");

assert.match(html, /class="wulff-evidence-card"/);
assert.match(html, /id="wulffGeometryPlot"/);
assert.match(html, /id="downloadWulffRequest"/);
assert.match(html, /id="wulffResponseInput"/);
assert.match(html, /illustrative only/);
assert.match(html, /this evidence does not rank growth/);
assert.match(app, /external-interfacial-energy\.mjs\?v=20260831-353/);
assert.match(app, /buildInterfacialEnergyRequest/);
assert.match(app, /validateInterfacialEnergyResponse/);
assert.match(app, /interfacialEnergyEvidence: interfacialEnergyReceipt\(\)/);
assert.match(app, /morphology, facet frequency, undercoordination, and GCTS scores never supply γ/i);
assert.match(app, /candidateRankingChanged: false|candidateRankingChangedByBinding/);
assert.match(readme, /Build 353/);
assert.match(readme, /Opposite normals are not silently identified/);
assert.match(readme, /does \*\*not\*\* infer γ from the morphology/);

console.log("interfacial-energy portal contract passed");
