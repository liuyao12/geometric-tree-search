#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const required = [
  "balanced-1000",
  "balanced-2000",
  "balanced-2000-proof",
  "face-pocket",
  "face-constrained",
  "face-coverage",
  "crystal-training",
  "crystal-training-proof",
  "balanced-holdout",
  "crystal-holdout"
];
for (const name of required) assert.ok(args.get(name), `--${name}=<report.json> is required`);
const readJson = async path => JSON.parse(await readFile(path, "utf8"));
const readOne = name => readJson(args.get(name));
const readMany = async name => Promise.all(args.get(name).split(",").filter(Boolean).map(readJson));
const mergeReports = reports => {
  assert.ok(reports.length);
  assert.ok(reports.every(report => report.schemaVersion === reports[0].schemaVersion));
  return {
    ...reports[0],
    cases: reports.flatMap(report => report.cases),
    rows: reports.flatMap(report => report.rows)
  };
};
const [
  balanced1000,
  balanced2000,
  balanced2000Proof,
  facePocket,
  faceConstrained,
  faceCoverage,
  crystalTraining,
  crystalTrainingProof,
  balancedHoldoutReports,
  crystalHoldoutReports
] = await Promise.all([
  readOne("balanced-1000"),
  readOne("balanced-2000"),
  readOne("balanced-2000-proof"),
  readOne("face-pocket"),
  readOne("face-constrained"),
  readOne("face-coverage"),
  readOne("crystal-training"),
  readOne("crystal-training-proof"),
  readMany("balanced-holdout"),
  readMany("crystal-holdout")
]);
const balancedHoldout = mergeReports(balancedHoldoutReports);
const crystalHoldout = mergeReports(crystalHoldoutReports);
const reports = [
  balanced1000,
  balanced2000,
  balanced2000Proof,
  facePocket,
  faceConstrained,
  faceCoverage,
  crystalTraining,
  crystalTrainingProof,
  ...balancedHoldoutReports,
  ...crystalHoldoutReports
];
const benchmarkSchemaVersions = [...new Set(reports.map(report => report.schemaVersion))].sort();
assert.deepEqual(benchmarkSchemaVersions, [16, 17]);

const candidateIds = ["10_16113", "10_45026", "10_45033", "9_11683"];
const keyOf = row => `${row.case}:${row.seed}`;
const sortedRows = report => report.rows.slice().sort((left, right) =>
  candidateIds.indexOf(left.case) - candidateIds.indexOf(right.case)
  || left.seed - right.seed
);
const rowsByKey = report => new Map(sortedRows(report).map(row => [keyOf(row), row]));
const assertCaptured = row => {
  const milestone = row.growthMilestones?.at(-1);
  assert.ok(milestone, `${keyOf(row)} must have a captured growth milestone`);
  assert.equal(row.largestPatch, milestone.patchSize);
  assert.equal(row.witnessHash, milestone.witnessHash);
  assert.ok(row.maxLiveTiles >= row.largestPatch);
  assert.equal(row.uncapturedMaxLiveTiles, row.maxLiveTiles - row.largestPatch);
};
for (const report of reports) for (const row of report.rows) assertCaptured(row);

const compactMilestones = row => row.growthMilestones.map(milestone => ({
  patch_size: milestone.patchSize,
  visited_nodes: milestone.visitedNodes,
  backtracks: milestone.backtracks,
  elapsed_ms: milestone.elapsedMs,
  witness_hash: milestone.witnessHash
}));
const compact = (row, { milestones = true } = {}) => ({
  largest_patch: row.largestPatch,
  max_live_tiles: row.maxLiveTiles,
  uncaptured_max_live_tiles: row.uncapturedMaxLiveTiles,
  witness_hash: row.witnessHash,
  visited_nodes: row.visitedNodes,
  backtracks: row.backtracks,
  elapsed_ms: row.elapsedMs,
  termination_reason: row.terminationReason,
  face_order: row.faceOrder ?? "mrv",
  move_order: row.moveOrder,
  failure_memo_states: row.failureMemoStates,
  failure_memo_hits: row.failureMemoHits,
  max_frontier_points: row.maxFrontierPoints,
  max_candidate_count: row.maxCandidateCount,
  ...(milestones ? { growth_milestones: compactMilestones(row) } : {})
});
const compactProof = row => ({
  id: row.case,
  seed: row.seed,
  largest_patch: row.largestPatch,
  witness_hash: row.witnessHash,
  target_check_attempted: row.genericPeriodicCertificateTargetAttempted,
  target_check_completed: row.genericPeriodicCertificateTargetCompleted,
  target_check_timed_out: row.genericPeriodicCertificateTargetTimedOut,
  target_certificate_found: row.genericPeriodicCertificateTargetFound,
  check_elapsed_ms: row.genericPeriodicCertificateElapsedMs,
  patch_fingerprints: row.genericPeriodicCertificateCheckFingerprints
});
const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)];
};
const compare = (baselineRows, challengerRows, target = 60) => {
  assert.deepEqual(baselineRows.map(keyOf), challengerRows.map(keyOf));
  return {
    better: challengerRows.filter((row, index) => row.largestPatch > baselineRows[index].largestPatch).length,
    equal: challengerRows.filter((row, index) => row.largestPatch === baselineRows[index].largestPatch).length,
    worse: challengerRows.filter((row, index) => row.largestPatch < baselineRows[index].largestPatch).length,
    baseline_target_hits: baselineRows.filter(row => row.largestPatch >= target).length,
    challenger_target_hits: challengerRows.filter(row => row.largestPatch >= target).length
  };
};
const depthSummary = (rows, target = 60) => ({
  paths: rows.length,
  robust_largest_patch: Math.min(...rows.map(row => row.largestPatch)),
  median_largest_patch: median(rows.map(row => row.largestPatch)),
  best_largest_patch: Math.max(...rows.map(row => row.largestPatch)),
  target_hits: rows.filter(row => row.largestPatch >= target).length,
  total_visited_nodes: rows.reduce((sum, row) => sum + row.visitedNodes, 0),
  total_backtracks: rows.reduce((sum, row) => sum + row.backtracks, 0),
  observed_elapsed_ms: rows.reduce((sum, row) => sum + row.elapsedMs, 0)
});

const balanced1000Rows = sortedRows(balanced1000);
const balanced2000Rows = sortedRows(balanced2000);
const balanced2000ProofRows = rowsByKey(balanced2000Proof);
assert.deepEqual(balanced1000Rows.map(keyOf), balanced2000Rows.map(keyOf));
assert.ok(balanced2000Rows.every((row, index) => row.largestPatch >= balanced1000Rows[index].largestPatch));
for (const row of balanced2000Rows) {
  const proof = balanced2000ProofRows.get(keyOf(row));
  assert.deepEqual(
    [proof.largestPatch, proof.witnessHash, proof.visitedNodes, proof.backtracks],
    [row.largestPatch, row.witnessHash, row.visitedNodes, row.backtracks]
  );
}
const budgetTargetProofs = balanced2000Rows
  .filter(row => row.largestPatch >= 60)
  .map(row => compactProof(balanced2000ProofRows.get(keyOf(row))));

const faceReports = new Map([
  ["mrv", balanced1000],
  ["pocket", facePocket],
  ["constrained", faceConstrained],
  ["coverage", faceCoverage]
]);
const faceOrderPaths = balanced1000Rows.map(reference => ({
  id: reference.case,
  seed: reference.seed,
  outcomes: Object.fromEntries([...faceReports].map(([order, report]) => {
    const row = rowsByKey(report).get(keyOf(reference));
    assert.equal(row.faceOrder, order);
    assert.equal(row.moveOrder, "balanced");
    return [order, compact(row, { milestones: false })];
  }))
}));
const faceOrderSummary = Object.fromEntries([...faceReports].map(([order, report]) => [
  order,
  depthSummary(sortedRows(report))
]));
assert.ok(["pocket", "constrained", "coverage"].every(order =>
  faceOrderSummary.mrv.target_hits > faceOrderSummary[order].target_hits
  && faceOrderSummary.mrv.median_largest_patch > faceOrderSummary[order].median_largest_patch
));

const crystalTrainingRows = sortedRows(crystalTraining);
const balancedHoldoutRows = sortedRows(balancedHoldout);
const crystalHoldoutRows = sortedRows(crystalHoldout);
const trainingComparison = compare(balanced1000Rows, crystalTrainingRows);
const holdoutComparison = compare(balancedHoldoutRows, crystalHoldoutRows);
const combinedComparison = compare(
  [...balanced1000Rows, ...balancedHoldoutRows],
  [...crystalTrainingRows, ...crystalHoldoutRows]
);
assert.deepEqual(trainingComparison, {
  better: 8,
  equal: 0,
  worse: 4,
  baseline_target_hits: 1,
  challenger_target_hits: 3
});
assert.deepEqual(holdoutComparison, {
  better: 13,
  equal: 0,
  worse: 7,
  baseline_target_hits: 0,
  challenger_target_hits: 4
});

const balanced1000ProofByKey = balanced2000ProofRows;
const crystalTrainingProofByKey = rowsByKey(crystalTrainingProof);
const selectedTargetProofs = [];
for (const [policy, searchRows, proofByKey] of [
  ["balanced_training", balanced1000Rows, balanced1000ProofByKey],
  ["crystal_training", crystalTrainingRows, crystalTrainingProofByKey],
  ["balanced_holdout", balancedHoldoutRows, rowsByKey(balancedHoldout)],
  ["crystal_holdout", crystalHoldoutRows, rowsByKey(crystalHoldout)]
]) {
  for (const row of searchRows.filter(item => item.largestPatch >= 60)) {
    const proof = proofByKey.get(keyOf(row));
    assert.ok(proof, `${policy}/${keyOf(row)} must have an exact replay`);
    assert.deepEqual(
      [proof.largestPatch, proof.witnessHash, proof.visitedNodes, proof.backtracks],
      [row.largestPatch, row.witnessHash, row.visitedNodes, row.backtracks]
    );
    assert.equal(proof.genericPeriodicCertificateTargetCompleted, true);
    assert.equal(proof.genericPeriodicCertificateTargetTimedOut, false);
    assert.equal(proof.genericPeriodicCertificateTargetFound, false);
    selectedTargetProofs.push({ policy, ...compactProof(proof) });
  }
}

const moveOrderPaths = balanced1000Rows.map(trainingRow => ({
  id: trainingRow.case,
  seed: trainingRow.seed,
  split: "training",
  balanced: compact(trainingRow),
  crystal: compact(crystalTrainingRows.find(row => keyOf(row) === keyOf(trainingRow)))
})).concat(balancedHoldoutRows.map(holdoutRow => ({
  id: holdoutRow.case,
  seed: holdoutRow.seed,
  split: "holdout",
  balanced: compact(holdoutRow),
  crystal: compact(crystalHoldoutRows.find(row => keyOf(row) === keyOf(holdoutRow)))
})));
const candidateSummary = candidateIds.map(id => {
  const paths = moveOrderPaths.filter(path => path.id === id);
  const balancedRows = paths.map(path => path.balanced);
  const crystalRows = paths.map(path => path.crystal);
  return {
    id,
    paths: paths.length,
    crystal_better: paths.filter(path => path.crystal.largest_patch > path.balanced.largest_patch).length,
    crystal_equal: paths.filter(path => path.crystal.largest_patch === path.balanced.largest_patch).length,
    crystal_worse: paths.filter(path => path.crystal.largest_patch < path.balanced.largest_patch).length,
    balanced_robust_largest_patch: Math.min(...balancedRows.map(row => row.largest_patch)),
    balanced_median_largest_patch: median(balancedRows.map(row => row.largest_patch)),
    balanced_best_largest_patch: Math.max(...balancedRows.map(row => row.largest_patch)),
    balanced_target_hits: balancedRows.filter(row => row.largest_patch >= 60).length,
    crystal_robust_largest_patch: Math.min(...crystalRows.map(row => row.largest_patch)),
    crystal_median_largest_patch: median(crystalRows.map(row => row.largest_patch)),
    crystal_best_largest_patch: Math.max(...crystalRows.map(row => row.largest_patch)),
    crystal_target_hits: crystalRows.filter(row => row.largest_patch >= 60).length,
    crystal_distinct_target_witnesses: new Set(crystalRows
      .filter(row => row.largest_patch >= 60)
      .map(row => row.witness_hash)).size
  };
});

const targetFingerprintKeys = selectedTargetProofs.map(proof => `${proof.id}:${proof.witness_hash}`);
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commits: {
    budget_scaling: args.get("budget-engine-commit") ?? null,
    order_screen: args.get("order-engine-commit") ?? null
  },
  benchmark_schema_versions: benchmarkSchemaVersions,
  protocol: {
    candidate_ids: candidateIds,
    training_seeds: [1, 2, 3],
    holdout_seeds: [4, 5, 6, 7, 8],
    target_tiles: 60,
    baseline_node_limits: [1000, 2000],
    face_orders: [...faceReports.keys()],
    move_orders: ["balanced", "crystal"],
    frontier_order: "mrv",
    exact_target_check: "face-paired boundary quotient at every reached 60-tile target",
    witness_accounting: "largest_patch and witness_hash identify the last captured placement snapshot; max_live_tiles retains any transient uncaptured engine peak"
  },
  budget_scaling: {
    summary: {
      balanced_1000: depthSummary(balanced1000Rows),
      balanced_2000: depthSummary(balanced2000Rows),
      all_paths_non_decreasing: true,
      exact_target_checks_completed: budgetTargetProofs.length,
      exact_target_checks_timed_out: budgetTargetProofs.filter(path => path.target_check_timed_out).length,
      periodic_certificates_found: budgetTargetProofs.filter(path => path.target_certificate_found).length
    },
    paths: balanced1000Rows.map((row, index) => ({
      id: row.case,
      seed: row.seed,
      balanced_1000: compact(row),
      balanced_2000: compact(balanced2000Rows[index]),
      balanced_2000_target_proof: budgetTargetProofs.find(path => path.id === row.case && path.seed === row.seed) ?? null
    }))
  },
  frontier_order_screen: {
    paths: faceOrderPaths,
    summary: faceOrderSummary,
    policy_decision: "retain_mrv"
  },
  move_order_screen: {
    paths: moveOrderPaths,
    candidate_summary: candidateSummary,
    training_comparison: trainingComparison,
    holdout_comparison: holdoutComparison,
    combined_comparison: combinedComparison,
    exact_target_proofs: selectedTargetProofs,
    exact_target_checks_completed: selectedTargetProofs.length,
    exact_target_checks_timed_out: selectedTargetProofs.filter(path => path.target_check_timed_out).length,
    periodic_certificates_found: selectedTargetProofs.filter(path => path.target_certificate_found).length,
    distinct_candidate_target_witnesses: new Set(targetFingerprintKeys).size,
    policy_decision: "add_crystal_as_complementary_proof_lane_retain_balanced"
  },
  interpretation: [
    "Increasing the balanced MRV budget from 1,000 to 2,000 nodes weakly deepens all 12 training paths and raises 60-tile target hits from one to four.",
    "MRV is the clear frontier-order control: it is the only tested order to reach 60 tiles and has a substantially higher median depth than pocket, constrained, or coverage order.",
    "Crystal move ordering improves 21 of 32 balanced paths and raises 60-tile target hits from one to seven, but worsens eleven paths, so it is complementary rather than a replacement.",
    "Crystal order is especially discriminating for 10_45026: four of eight paths reach 60 tiles, represented by two distinct witness hashes, while balanced reaches none.",
    "All eight selected 60-tile target checks completed without timeout or translational quotient certificate; these finite patches prove neither space tiling nor aperiodicity."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
