import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => fs.readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const css = read("apps/iqc-growth-live/style.css");
const moduleSource = read("apps/iqc-growth-live/classical-capillarity-action.mjs");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");
const readme = read("apps/iqc-growth-live/README.md");
const methods = read("docs/projects/materials-recursive-gcts-benchmark.md");

for (const token of ["evaluateClassicalCapillarityAction",
  "matchedClassicalCapillarityRankingAudit", "frozen-center Wulff scale",
  "deltaWorkElectronVolt", "beforeNormalizedSupportResidual",
  "candidateSetChanged: false", "hardAdmissionChanged: false",
  "atomCountInferred: false", "nucleationRateInferred: false", "targetUsed: false"])
  assert.ok(moduleSource.includes(token), token);

for (const token of ["id=\"classicalCapillarityModeSelect\"",
  "Rank by conditional ΔΔG", "id=\"classicalCapillarityWeightSelect\"",
  "id=\"classicalCapillarityRankingGate\"", "id=\"classicalCapillarityRankingState\"",
  "id=\"classicalCapillarityRankingAudit\"", "favorable / uphill"])
  assert.ok(html.includes(token), token);

for (const token of ["classical-capillarity-action.mjs?v=20260901-419",
  "function classicalCapillarityGate()", "function classicalCapillarityForFreshSites",
  "function captureClassicalCapillarityMatchedRankingAudit(entries)",
  "function renderClassicalCapillarityRankingControls()", "activeClassicalCapillarityWeight()",
  "evaluation.classicalCapillarity.score", "captureClassicalCapillarityMatchedRankingAudit(evaluated)",
  "validatedClassicalCapillarityRanking", "buildId: \"20260901-419\""])
  assert.ok(app.includes(token), token);

assert.ok(css.includes(".classical-capillarity-ranking"));
assert.ok(atlas.includes("Conditional capillarity action ranking"));
assert.ok(atlas.includes("ΔΔG = Δ[Cγs^(d−1) − ΔgV₀s^d]"));
assert.ok(readme.includes("Build 411 · capillarity work becomes an optional geometric action prior"));
assert.ok(methods.includes("Matched conditional capillarity action prior (Build 411)"));
assert.ok(html.includes("app.js?v=20260901-419"));
assert.ok(html.includes("style.css?v=20260901-419"));
assert.ok(html.includes("evidence-atlas.js?v=20260901-419"));

console.log("classical capillarity action portal contract: passed");
