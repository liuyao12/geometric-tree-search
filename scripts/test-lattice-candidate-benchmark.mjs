import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { GeometricFailureMemo } from "../assets/geometric-failure-memo.js";

const translatedClauseProbe = new GeometricFailureMemo({
  contextMatch: "subset",
  describePlacement: placement => placement
});
translatedClauseProbe.encode(
  [
    { kind: "tile", orientation: "o0", translation: [0, 0, 0] },
    { kind: "tile", orientation: "o1", translation: [0, 1, 0] }
  ],
  { kind: "tile", orientation: "o2", translation: [1, 0, 0] }
);
assert.equal(
  translatedClauseProbe.compatible(
    { kind: "tile", orientation: "o2", translation: [11, -4, 3] },
    [
      { kind: "tile", orientation: "o0", translation: [10, -4, 3] },
      { kind: "tile", orientation: "o1", translation: [10, -3, 3] },
      { kind: "extra", orientation: "e0", translation: [8, -4, 3] }
    ]
  ),
  false,
  "a complete translated failed context must be rejected inside a larger patch"
);
assert.equal(
  translatedClauseProbe.compatible(
    { kind: "tile", orientation: "o2", translation: [11, -4, 3] },
    [{ kind: "tile", orientation: "o0", translation: [10, -4, 3] }]
  ),
  true,
  "a partial context must not trigger the full-context nogood"
);

const benchmark = new URL("./benchmark-lattice-candidate-suite.mjs", import.meta.url);
const run = argumentsList => {
  const result = spawnSync(process.execPath, [benchmark.pathname, ...argumentsList], {
    encoding: "utf8",
    timeout: 20000
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return JSON.parse(result.stdout);
};

const controls = run([
  "--ids=8_2480,10_27010",
  "--target=8",
  "--time-ms=200",
  "--exact-time-ms=2000",
  "--isohedral-horizon=24"
]);
assert.equal(controls.controlGatesPassed, true);
assert.deepEqual(controls.controls, {
  translationalControl: true,
  isohedralControl: true,
  nonTilerControl: true,
  aperiodicControl: true
});
assert.equal(
  controls.rows.find(row => row.case === "10_27010" && row.lane === "isohedral")?.certificatePatchSize,
  24
);

const survivor = run([
  "--ids=10_45026",
  "--special-controls=false",
  "--target=8",
  "--time-ms=150",
  "--exact-time-ms=200",
  "--isohedral-horizon=24"
]);
assert.equal(survivor.controlGatesPassed, true, "filtered benchmark runs must not require omitted controls");
assert.ok(survivor.rows.some(row => row.lane === "free_range"));
assert.ok(survivor.rows.some(row => row.lane === "free_range_no_brainer"));
assert.ok(survivor.rows.every(row => row.largestPatch >= 1));
assert.equal(survivor.rows.find(row => row.lane === "free_range")?.moveOrder, "balanced");
assert.equal(survivor.rows.find(row => row.lane === "free_range_no_brainer")?.moveOrder, "no_brainer");
assert.ok(["balanced", "no_brainer"].includes(survivor.unresolved[0].preferredFreeRangePolicy));
assert.equal(survivor.schemaVersion, 6);
assert.deepEqual(survivor.configuration.seeds, [1, 2, 3]);
const portfolioLanes = new Set(["free_range", "free_range_no_brainer"]);
const freeRangeRows = survivor.rows.filter(row => portfolioLanes.has(row.lane));
assert.equal(freeRangeRows.length, 6);
assert.ok(freeRangeRows.every(row => row.seed === row.effectiveSeed));
const expectedTargetHits = freeRangeRows
  .filter(row => row.largestPatch >= survivor.configuration.target)
  .map(row => row.lane === "free_range" ? "balanced" : "no_brainer");
const expectedPoliciesAtTarget = [...new Set(expectedTargetHits)].sort();
assert.deepEqual(
  survivor.unresolved[0].freeRangePortfolio.policiesReachingTarget.sort(),
  expectedPoliciesAtTarget
);
assert.equal(
  survivor.unresolved[0].freeRangePortfolio.outcome,
  expectedTargetHits.length === freeRangeRows.length
    ? "robust_target_reached"
    : expectedTargetHits.length
      ? "policy_or_seed_sensitive_target_reached"
      : "bounded_below_target"
);
assert.equal(
  survivor.unresolved[0].freeRangePortfolio.robustLargestPatch,
  Math.min(...freeRangeRows.map(row => row.largestPatch))
);
assert.equal(
  survivor.unresolved[0].freeRangePortfolio.bestLargestPatch,
  Math.max(...freeRangeRows.map(row => row.largestPatch))
);
assert.ok(survivor.unresolved[0].freeRangePortfolio.combinedVisitedNodes >= 2);
assert.equal(survivor.unresolved[0].freeRangePortfolio.trialCount, 6);
assert.equal(survivor.unresolved[0].freeRangePortfolio.targetHitCount, expectedTargetHits.length);
assert.equal(
  survivor.unresolved[0].freeRangePortfolio.targetHitRate,
  expectedTargetHits.length / freeRangeRows.length
);
assert.equal(survivor.unresolved[0].freeRangeUnbanded.lane, "free_range_unbanded");
assert.equal(survivor.unresolved[0].freeRangeUnbanded.generationLagCap, null);
assert.equal(survivor.unresolved[0].freeRangeUnbanded.failureMemoEnabled, true);
assert.equal(survivor.configuration.geometricNogood, false);
assert.equal(survivor.unresolved[0].freeRangeUnbanded.geometricNogoodEnabled, false);
assert.ok(freeRangeRows.every(row => row.failureMemoEnabled === false));
assert.ok(["inconclusive", "reject_certified_non_tiler"].includes(survivor.unresolved[0].screeningConclusion));

const nodeLimited = run([
  "--ids=10_45026",
  "--special-controls=false",
  "--target=24",
  "--time-ms=1000",
  "--exact-time-ms=1000",
  "--node-limit=1",
  "--seeds=7",
  "--failure-memo=false"
]);
const limitedFreeRangeRows = nodeLimited.rows.filter(row => portfolioLanes.has(row.lane));
assert.equal(limitedFreeRangeRows.length, 2);
assert.ok(limitedFreeRangeRows.every(row => row.seed === 7 && row.effectiveSeed === 7));
assert.ok(limitedFreeRangeRows.every(row => row.terminationReason === "node_limit"));
assert.equal(nodeLimited.configuration.failureMemo, false);
assert.equal(nodeLimited.unresolved[0].freeRangeUnbanded.failureMemoEnabled, false);
assert.deepEqual(
  nodeLimited.unresolved[0].freeRangePortfolio.policySummaries.balanced.terminationReasons,
  { node_limit: 1 }
);

const memoProbe = run([
  "--ids=10_45026",
  "--lanes=free_range_unbanded",
  "--special-controls=false",
  "--target=24",
  "--time-ms=5000",
  "--exact-time-ms=5000",
  "--node-limit=200",
  "--seeds=1",
  "--geometric-nogood=false"
]);
const memoRow = memoProbe.unresolved[0].freeRangeUnbanded;
assert.equal(memoRow.terminationReason, "node_limit");
assert.equal(memoRow.failureMemoEnabled, true);
assert.ok(memoRow.failureMemoStates >= 100, "candidate 10_45026 must populate the exact failure memo");
assert.ok(memoRow.failureMemoHits >= 20, "candidate 10_45026 must exercise duplicate-state reuse");
assert.equal(memoRow.failureMemoCapacityReached, false);
const memoAblation = run([
  "--ids=10_45026",
  "--lanes=free_range_unbanded",
  "--special-controls=false",
  "--target=24",
  "--time-ms=5000",
  "--exact-time-ms=5000",
  "--node-limit=200",
  "--seeds=1",
  "--failure-memo=false",
  "--geometric-nogood=false"
]);
const ablationRow = memoAblation.unresolved[0].freeRangeUnbanded;
assert.equal(ablationRow.failureMemoEnabled, false);
assert.equal(ablationRow.failureMemoHits, 0);
assert.deepEqual(
  [memoRow.resultKind, memoRow.terminationReason, memoRow.largestPatch, memoRow.visitedNodes, memoRow.backtracks],
  [ablationRow.resultKind, ablationRow.terminationReason, ablationRow.largestPatch, ablationRow.visitedNodes, ablationRow.backtracks],
  "exact failure memoization must preserve the bounded search result"
);

const nogoodProbe = run([
  "--ids=10_45026",
  "--lanes=free_range_unbanded",
  "--special-controls=false",
  "--target=24",
  "--time-ms=5000",
  "--exact-time-ms=5000",
  "--node-limit=200",
  "--seeds=1",
  "--geometric-nogood=true"
]);
const nogoodRow = nogoodProbe.unresolved[0].freeRangeUnbanded;
assert.equal(nogoodRow.geometricNogoodEnabled, true);
assert.ok(nogoodRow.geometricNogoodClauses >= 1000);
assert.ok(nogoodRow.geometricNogoodPrunes >= 400);
assert.ok(
  nogoodRow.largestPatch >= ablationRow.largestPatch + 4,
  "translation-equivariant full-context nogoods must deepen the fixed-node 10_45026 proof search"
);
assert.equal(nogoodRow.terminationReason, "node_limit");
assert.equal(nogoodRow.geometricNogoodCapacityReached, false);
assert.equal(nogoodRow.geometricNogoodPivotIndex, true);
assert.ok(nogoodRow.geometricNogoodAvoidedClauseChecks >= 3_000_000);
assert.ok(
  nogoodRow.geometricNogoodClauseChecks * 20 < nogoodRow.geometricNogoodLinearClauseChecks,
  "pivot indexing must avoid at least 95% of the reference linear clause checks"
);
const linearNogoodProbe = run([
  "--ids=10_45026",
  "--lanes=free_range_unbanded",
  "--special-controls=false",
  "--target=24",
  "--time-ms=5000",
  "--exact-time-ms=5000",
  "--node-limit=200",
  "--seeds=1",
  "--geometric-nogood=true",
  "--geometric-nogood-index=false"
]);
const linearNogoodRow = linearNogoodProbe.unresolved[0].freeRangeUnbanded;
assert.equal(linearNogoodRow.geometricNogoodPivotIndex, false);
assert.deepEqual(
  [
    nogoodRow.resultKind,
    nogoodRow.terminationReason,
    nogoodRow.largestPatch,
    nogoodRow.visitedNodes,
    nogoodRow.backtracks,
    nogoodRow.geometricNogoodClauses,
    nogoodRow.geometricNogoodPrunes
  ],
  [
    linearNogoodRow.resultKind,
    linearNogoodRow.terminationReason,
    linearNogoodRow.largestPatch,
    linearNogoodRow.visitedNodes,
    linearNogoodRow.backtracks,
    linearNogoodRow.geometricNogoodClauses,
    linearNogoodRow.geometricNogoodPrunes
  ],
  "pivot indexing must preserve every bounded nogood-search decision"
);
assert.ok(nogoodRow.geometricNogoodClauseChecks * 20 < linearNogoodRow.geometricNogoodClauseChecks);

console.log("Lattice candidate benchmark regressions passed", {
  controls: controls.rows.length,
  survivorPolicies: survivor.rows.filter(row => row.lane.startsWith("free_range")).length
});
