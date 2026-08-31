import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  evaluateWulffShapeRegularizer,
  matchedWulffRankingAudit,
  orientedEnergyKernelEstimate,
} from "../apps/iqc-growth-live/wulff-shape-regularizer.mjs";

const html = readFileSync(new URL("../apps/iqc-growth-live/index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const normalization = readFileSync(new URL("../apps/iqc-growth-live/score-normalization.mjs", import.meta.url), "utf8");

for (const id of ["wulffRankingModeSelect", "wulffAngularReachSelect",
  "wulffRegularizerWeightSelect", "wulffRankingAudit"]) assert.match(html, new RegExp(`id="${id}"`));
assert.match(html, /Display only · no frontier effect/);
assert.match(html, /Shape regularizer · unchanged candidates/);
assert.match(app, /evaluateWulffShapeRegularizer/);
assert.match(app, /captureWulffMatchedRankingAudit\(evaluated\)/);
assert.match(app, /candidateSetChanged: false, candidateGeometryChanged: false, hardAdmissionChanged: false/);
assert.match(app, /usedAsAttachmentRate: false/);
assert.match(normalization, /"wulff-shape": spec/);
assert.match(normalization, /"wulff-shape": "interfacial-free-energy"/);

const orientations = [
  { orientationId: "+x", normal: [1, 0], interfacialFreeEnergy: 1, uncertainty: .01 },
  { orientationId: "-x", normal: [-1, 0], interfacialFreeEnergy: 2, uncertainty: .01 },
  { orientationId: "+y", normal: [0, 1], interfacialFreeEnergy: 1, uncertainty: .01 },
  { orientationId: "-y", normal: [0, -1], interfacialFreeEnergy: 1, uncertainty: .01 },
];
assert.equal(orientedEnergyKernelEstimate(orientations, [1, 0], Math.PI / 12).interfacialFreeEnergy, 1);
assert.equal(orientedEnergyKernelEstimate(orientations, [-1, 0], Math.PI / 12).interfacialFreeEnergy, 2);
assert.equal(orientedEnergyKernelEstimate(orientations, [Math.SQRT1_2, Math.SQRT1_2], Math.PI / 12).supported, false);

const regularizer = evaluateWulffShapeRegularizer({
  occupiedPositions: [[-.8, -1.2, 0], [.8, -1.2, 0], [.8, 1.2, 0], [-.8, 1.2, 0]],
  emittedPositions: [[1, 0, 0]], orientationBasisCartesian: [[1, 0, 0], [0, 1, 0]],
  orientations: orientations.map((entry) => ({ ...entry,
    interfacialFreeEnergy: entry.orientationId === "-x" ? 1 : entry.interfacialFreeEnergy })),
  maximumAngleRadians: Math.PI / 6,
});
assert.equal(regularizer.supported, true);
assert.ok(regularizer.score > 0);
assert.equal(regularizer.candidateSetChanged, false);
assert.equal(regularizer.targetUsed, false);

const ranking = matchedWulffRankingAudit([
  { candidateId: "a", baselineScore: 2, regularizedScore: 1, supported: true },
  { candidateId: "b", baselineScore: 1, regularizedScore: 2, supported: false },
]);
assert.equal(ranking.rankInversions, 1);
assert.equal(ranking.candidateSetIdentical, true);

console.log("Wulff shape-regularizer portal contract passed");
