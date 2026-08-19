import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

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
assert.equal(survivor.schemaVersion, 3);
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
assert.ok(["inconclusive", "reject_certified_non_tiler"].includes(survivor.unresolved[0].screeningConclusion));

const nodeLimited = run([
  "--ids=10_45026",
  "--special-controls=false",
  "--target=24",
  "--time-ms=1000",
  "--exact-time-ms=1000",
  "--node-limit=1",
  "--seeds=7"
]);
const limitedFreeRangeRows = nodeLimited.rows.filter(row => portfolioLanes.has(row.lane));
assert.equal(limitedFreeRangeRows.length, 2);
assert.ok(limitedFreeRangeRows.every(row => row.seed === 7 && row.effectiveSeed === 7));
assert.ok(limitedFreeRangeRows.every(row => row.terminationReason === "node_limit"));
assert.deepEqual(
  nodeLimited.unresolved[0].freeRangePortfolio.policySummaries.balanced.terminationReasons,
  { node_limit: 1 }
);

console.log("Lattice candidate benchmark regressions passed", {
  controls: controls.rows.length,
  survivorPolicies: survivor.rows.filter(row => row.lane.startsWith("free_range")).length
});
