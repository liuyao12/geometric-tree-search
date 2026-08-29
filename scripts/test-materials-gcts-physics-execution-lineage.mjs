import assert from "node:assert/strict";

import {
  buildPhysicsEffectMatrix,
  buildPhysicsInvestigationProtocol,
  buildPhysicsScoreExecutionCoverage,
  PHYSICS_ABLATION_CONTROL_BINDINGS,
  physicsExecutionLineage,
} from "../apps/iqc-growth-live/physics-compression-map.js";
import { SCORE_PHYSICS_MANIFEST_IDS } from "../apps/iqc-growth-live/score-normalization.mjs";

const activeRecords = [
  {
    id: "collinear-spin",
    process: "scalar spin overlap color",
    status: "hard",
    role: "transported exact overlap color",
    encoding: "signed scalar labels",
    evidence: "one overlap rejected",
    boundary: "not a spin Hamiltonian",
    controlRouteAvailable: true,
  },
  {
    id: "long-range",
    process: "collective graph response",
    status: "soft",
    role: "screened accepted-history graph field",
    encoding: "screened graph mark",
    evidence: "candidate score audited",
    boundary: "not long-range elasticity",
    controlRouteAvailable: true,
  },
  {
    id: "configurational-entropy",
    process: "continuation multiplicity",
    status: "soft",
    role: "fit-only frozen-grammar look-ahead",
    encoding: "effective outgoing-rule count",
    evidence: "candidate score audited",
    boundary: "not thermodynamic entropy",
    controlRouteAvailable: true,
  },
  {
    id: "constraint-rigidity",
    process: "constraint dimensionality",
    status: "soft",
    role: "unit-contact direction-tensor ordering",
    encoding: "normalized contact tensor",
    evidence: "candidate score audited",
    boundary: "not a Hessian",
    controlRouteAvailable: true,
  },
];

const spin = physicsExecutionLineage(activeRecords[0]);
assert.equal(spin.hardAdmissionCanChange, true);
assert.equal(spin.diagnosticOnly, false);
assert.deepEqual(spin.effects, ["hard admission"]);
assert.deepEqual(spin.executionObjects, ["candidate acceptance / rejection"]);

for (const record of activeRecords.slice(1)) {
  const lineage = physicsExecutionLineage(record);
  assert.equal(lineage.rankingCanChange, true, `${record.id} must expose its live rank hook`);
  assert.equal(lineage.diagnosticOnly, false);
  assert.deepEqual(lineage.effects, ["soft branch ranking"]);
  assert.deepEqual(lineage.executionObjects, ["signed candidate score and branch rank"]);
  assert.equal(PHYSICS_ABLATION_CONTROL_BINDINGS[record.id].ablationValue, "none");
}

const matrix = buildPhysicsEffectMatrix(activeRecords);
assert.equal(matrix.counts.hardAdmission, 1);
assert.equal(matrix.counts.ranking, 3);
assert.equal(matrix.counts.diagnostic, 0);
assert.equal(matrix.readinessCounts.executing, 4);

const protocol = buildPhysicsInvestigationProtocol(
  activeRecords,
  activeRecords.map((record) => record.id),
);
assert.equal(protocol.selectedRecordCount, 4);
assert.equal(protocol.effectCoverage.hardAdmission.count, 1);
assert.equal(protocol.effectCoverage.ranking.count, 3);
assert.deepEqual(protocol.blockingRecordIds, []);

const inactiveRank = physicsExecutionLineage({ ...activeRecords[1], status: "open", role: "diagnostic" });
assert.equal(inactiveRank.rankingCanChange, false);
assert.equal(inactiveRank.diagnosticOnly, true);

const mixedLocal = {
  id: "local",
  process: "local bonding geometry",
  status: "hard",
  role: "hard gate + optional rank",
  encoding: "colored contact and angle envelopes",
  evidence: "candidate checks",
  boundary: "not bond energy",
  executionEffects: { hardAdmission: true, ranking: true },
};
const mixedLineage = physicsExecutionLineage(mixedLocal);
assert.equal(mixedLineage.hardAdmissionCanChange, true);
assert.equal(mixedLineage.rankingCanChange, true);
assert.deepEqual(mixedLineage.executionObjects, [
  "candidate acceptance / rejection",
  "signed candidate score and branch rank",
]);
const localGateOnly = physicsExecutionLineage({
  ...mixedLocal,
  executionEffects: { hardAdmission: true, ranking: false },
});
assert.equal(localGateOnly.hardAdmissionCanChange, true);
assert.equal(localGateOnly.rankingCanChange, false);

const connection = {
  id: "connection",
  process: "cluster attachment",
  status: "learned",
  role: "learned local connection gate / rank",
  encoding: "finite ports",
  evidence: "candidate checks",
  boundary: "not attachment free energy",
};
const scoreTerms = [
  { id: "grammar-priority", weight: 1, normalization: { physicsManifestId: "connection" } },
  { id: "geometric-strain", weight: -.16, normalization: { physicsManifestId: "local" } },
  { id: "known-window-gain", weight: 2.5, normalization: { physicsManifestId: "score-ledger" } },
  { id: "exploration", weight: 1, normalization: { physicsManifestId: "path-ensemble" } },
];
const coverage = buildPhysicsScoreExecutionCoverage(scoreTerms, [connection, mixedLocal]);
assert.equal(coverage.complete, true);
assert.equal(coverage.activeRankTermCount, 2);
assert.equal(coverage.coveredRankTermCount, 2);
assert.deepEqual(coverage.excludedTermIds, ["known-window-gain", "exploration"]);

const missingCoverage = buildPhysicsScoreExecutionCoverage([
  { id: "unknown", weight: 1, normalization: { physicsManifestId: "missing" } },
], [connection]);
assert.equal(missingCoverage.complete, false);
assert.deepEqual(missingCoverage.unmappedTermIds, ["unknown"]);

const nonRankingCoverage = buildPhysicsScoreExecutionCoverage([
  { id: "geometric-strain", weight: -.16, normalization: { physicsManifestId: "local" } },
], [{ ...mixedLocal, executionEffects: { hardAdmission: true, ranking: false } }]);
assert.equal(nonRankingCoverage.complete, false);
assert.deepEqual(nonRankingCoverage.nonRankingTermIds, ["geometric-strain"]);

// Every score term in the frozen normalization vocabulary must resolve to a
// ranking-capable manifest layer.  The two search-ledger terms are deliberately
// outside the physics lineage certificate and are excluded by the helper.
const completeVocabularyTerms = Object.entries(SCORE_PHYSICS_MANIFEST_IDS).map(
  ([id, physicsManifestId]) => ({ id, weight: 1, normalization: { physicsManifestId } }),
);
const completeVocabularyRecords = [...new Set(Object.values(SCORE_PHYSICS_MANIFEST_IDS))]
  .filter((id) => !["score-ledger", "path-ensemble"].includes(id))
  .map((id) => ({
    id,
    process: id,
    status: "soft",
    role: "candidate rank",
    encoding: "frozen geometric channel",
    evidence: "score receipt",
    boundary: "not a physical potential",
  }));
const completeVocabularyCoverage = buildPhysicsScoreExecutionCoverage(
  completeVocabularyTerms,
  completeVocabularyRecords,
);
assert.equal(completeVocabularyCoverage.complete, true);
assert.equal(
  completeVocabularyCoverage.activeRankTermCount,
  completeVocabularyTerms.length - 2,
);
assert.deepEqual(completeVocabularyCoverage.unmappedTermIds, []);
assert.deepEqual(completeVocabularyCoverage.nonRankingTermIds, []);

console.log("physics execution lineage contract passed");
