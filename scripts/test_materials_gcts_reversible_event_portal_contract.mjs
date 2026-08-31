import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const app = await readFile(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const html = await readFile(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const readme = await readFile(new URL("../apps/iqc-growth-live/README.md", import.meta.url), "utf8");

assert.match(html, /id="actionBarrierCatalog"/);
assert.match(html, /value="forward-only"/);
assert.match(html, /value="reversible-leaves" selected/);
assert.match(html, /app\.js\?v=20260831-384/);
assert.match(html, /Microscopic inverse lineage/);
assert.match(html, /id="transitionNetworkPlot"/);
assert.match(html, /id="transitionNetworkCycleSelect"/);
assert.match(html, /id="transitionPathSource"/);
assert.match(html, /id="transitionPathTarget"/);
assert.match(html, /id="finiteNucleationPlot"/);

assert.match(app, /enumerateDetachableLeafPlacements/);
assert.match(app, /performOwnershipCertifiedDetachment/);
assert.match(app, /projected detachment does not match the frozen final-state geometry digest/);
assert.match(app, /thermodynamicReversibilityCertified: false/);
assert.match(app, /detailedBalanceCertified: false/);
assert.match(app, /registerCommittedReversibleTransition/);
assert.match(app, /microscopic-inverse-lineage/);
assert.match(app, /finitePairLocalBalancePassed/);
assert.match(app, /grandCanonicalEvidence/);
assert.match(app, /buildFiniteTransitionNetwork/);
assert.match(app, /finite-transition-network/);
assert.match(app, /finite-transition-pathways/);
assert.match(app, /finite-transition-pathway/);
assert.match(app, /finite-nucleation-landscape/);

assert.match(readme, /Build 347/);
assert.match(readme, /Build 348/);
assert.match(readme, /Build 349/);
assert.match(readme, /Build 350/);
assert.match(readme, /Build 351/);
assert.match(readme, /Build 352/);
assert.match(readme, /does\s+not manufacture thermodynamics/);

console.log("reversible event portal integration: passed");
