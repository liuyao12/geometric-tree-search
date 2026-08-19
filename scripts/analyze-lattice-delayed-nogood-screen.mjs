#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const required = [
  "baseline",
  "immediate",
  "delayed-25",
  "delayed-50",
  "delayed-100",
  "delayed-proof",
  "baseline-fingerprint-report",
  "immediate-proof-report"
];
for (const name of required) assert.ok(args.get(name), `--${name}=<report.json> is required`);
const readJson = async name => JSON.parse(await readFile(args.get(name), "utf8"));
const normalizeCapturedWitnesses = report => ({
  ...report,
  rows: report.rows.map(row => {
    const milestone = row.growthMilestones?.at(-1);
    const maxLiveTiles = row.maxLiveTiles ?? row.largestPatch;
    if (!milestone) return {
      ...row,
      maxLiveTiles,
      uncapturedMaxLiveTiles: Math.max(0, maxLiveTiles - row.largestPatch)
    };
    assert.ok(maxLiveTiles >= milestone.patchSize);
    return {
      ...row,
      largestPatch: milestone.patchSize,
      witnessHash: milestone.witnessHash,
      maxLiveTiles,
      uncapturedMaxLiveTiles: maxLiveTiles - milestone.patchSize
    };
  })
});
const [
  baselineRaw,
  immediateRaw,
  delayed25Raw,
  delayed50Raw,
  delayed100Raw,
  delayedProofRaw,
  baselineFingerprintReport,
  immediateProofReport
] = await Promise.all(required.map(readJson));
const baseline = normalizeCapturedWitnesses(baselineRaw);
const immediate = normalizeCapturedWitnesses(immediateRaw);
const delayed25 = normalizeCapturedWitnesses(delayed25Raw);
const delayed50 = normalizeCapturedWitnesses(delayed50Raw);
const delayed100 = normalizeCapturedWitnesses(delayed100Raw);
const delayedProof = normalizeCapturedWitnesses(delayedProofRaw);

const thresholds = new Map([
  [25, delayed25],
  [50, delayed50],
  [100, delayed100]
]);
const searchReports = [baseline, immediate, ...thresholds.values()];
assert.ok(searchReports.every(report => report.schemaVersion === baseline.schemaVersion));
assert.equal(baseline.configuration.geometricNogood, false);
assert.equal(immediate.configuration.geometricNogood, true);
assert.equal(immediate.configuration.geometricNogoodActivationFailures ?? 0, 0);
for (const [threshold, report] of thresholds) {
  assert.equal(report.configuration.geometricNogood, true);
  assert.equal(report.configuration.geometricNogoodActivationFailures, threshold);
}
assert.equal(delayedProof.configuration.geometricNogood, true);
assert.equal(delayedProof.configuration.geometricNogoodActivationFailures, 25);

const without = (object, omitted) => Object.fromEntries(
  Object.entries(object).filter(([key]) => !omitted.includes(key))
);
const searchVariantKeys = ["geometricNogood", "geometricNogoodActivationFailures"];
for (const report of searchReports.slice(1)) {
  assert.deepEqual(
    without(report.configuration, searchVariantKeys),
    without(baseline.configuration, searchVariantKeys),
    "search sweep configurations may differ only in the nogood policy"
  );
}
const exactConfigKeys = [
  "genericPeriodicCertificate",
  "genericPeriodicCheckpoints",
  "genericPeriodicDistinctPatches",
  "genericPeriodicSamplingPolicy",
  "genericPeriodicSamplingStride",
  "genericPeriodicSamplingPrefix",
  "genericPeriodicMaxChecksPerSize",
  "genericPeriodicMaxTotalChecks",
  "genericPeriodicCheckpointTotalTimeMs",
  "genericPeriodicCertificateTimeMs"
];
assert.deepEqual(
  without(delayedProof.configuration, exactConfigKeys),
  without(delayed25.configuration, exactConfigKeys),
  "exact checking must be the only difference from the delayed-25 search arm"
);

const rowKey = row => `${row.case}:${row.seed}`;
const rowsByKey = report => new Map(report.rows.map(row => [rowKey(row), row]));
const baselineRows = rowsByKey(baseline);
const immediateRows = rowsByKey(immediate);
const delayedRows = new Map([...thresholds].map(([threshold, report]) => [threshold, rowsByKey(report)]));
const proofRows = rowsByKey(delayedProof);
const pathKeys = [...baselineRows.keys()];
assert.equal(pathKeys.length, 12);
for (const report of [...searchReports.slice(1), delayedProof]) {
  assert.deepEqual([...rowsByKey(report).keys()], pathKeys, "every policy must cover the same ordered paths");
}

const pathFields = row => [
  row.case,
  row.seed,
  row.largestPatch,
  row.witnessHash,
  row.visitedNodes,
  row.backtracks,
  row.terminationReason
];
for (const key of pathKeys) {
  assert.deepEqual(
    pathFields(proofRows.get(key)),
    pathFields(delayedRows.get(25).get(key)),
    `${key}: exact checkpoint checking changed the delayed search path`
  );
}

const compactMilestones = row => row.growthMilestones.map(milestone => ({
  patch_size: milestone.patchSize,
  visited_nodes: milestone.visitedNodes,
  backtracks: milestone.backtracks,
  elapsed_ms: milestone.elapsedMs,
  witness_hash: milestone.witnessHash
}));
const compactOutcome = row => ({
  largest_patch: row.largestPatch,
  max_live_tiles: row.maxLiveTiles,
  uncaptured_max_live_tiles: row.uncapturedMaxLiveTiles,
  witness_hash: row.witnessHash,
  visited_nodes: row.visitedNodes,
  backtracks: row.backtracks,
  elapsed_ms: row.elapsedMs,
  termination_reason: row.terminationReason,
  nogood_failure_states: row.geometricNogoodFailureStates,
  nogood_clauses: row.geometricNogoodClauses,
  nogood_prunes: row.geometricNogoodPrunes,
  nogood_activated: row.geometricNogoodActivated
    ?? (row.geometricNogoodEnabled && (row.geometricNogoodActivationFailureStates ?? 0) === 0)
});
const paths = pathKeys.map(key => {
  const baselineRow = baselineRows.get(key);
  const immediateRow = immediateRows.get(key);
  const delayed = Object.fromEntries([...delayedRows].map(([threshold, rows]) => [
    threshold,
    compactOutcome(rows.get(key))
  ]));
  return {
    id: baselineRow.case,
    seed: baselineRow.seed,
    baseline: compactOutcome(baselineRow),
    immediate: compactOutcome(immediateRow),
    delayed,
    immediate_to_delayed_25_patch_delta: delayed[25].largest_patch - immediateRow.largestPatch,
    baseline_to_delayed_25_patch_delta: delayed[25].largest_patch - baselineRow.largestPatch,
    baseline_growth_milestones: compactMilestones(baselineRow),
    delayed_25_growth_milestones: compactMilestones(delayedRows.get(25).get(key))
  };
});

const digest = values => createHash("sha256").update(values.slice().sort().join("\n")).digest("hex");
const proofPaths = pathKeys.map(key => {
  const row = proofRows.get(key);
  assert.equal(row.genericPeriodicCertificateChecksAttempted, row.genericPeriodicCertificateChecksCompleted);
  assert.equal(row.genericPeriodicCertificateChecksTimedOut, 0);
  assert.equal(row.genericPeriodicCertificateFound, false);
  const fingerprints = row.genericPeriodicCertificateCheckFingerprints;
  return {
    id: row.case,
    seed: row.seed,
    largest_patch: row.largestPatch,
    max_live_tiles: row.maxLiveTiles,
    uncaptured_max_live_tiles: row.uncapturedMaxLiveTiles,
    witness_hash: row.witnessHash,
    checks_attempted: row.genericPeriodicCertificateChecksAttempted,
    checks_completed: row.genericPeriodicCertificateChecksCompleted,
    checks_timed_out: row.genericPeriodicCertificateChecksTimedOut,
    certificate_found: row.genericPeriodicCertificateFound,
    target_check_attempted: row.genericPeriodicCertificateTargetAttempted,
    target_check_completed: row.genericPeriodicCertificateTargetCompleted,
    target_certificate_found: row.genericPeriodicCertificateTargetFound,
    fingerprint_digest_sha256: digest(fingerprints),
    fingerprints
  };
});

const baselineFingerprintCandidates = new Map(
  baselineFingerprintReport.candidates.map(candidate => [candidate.id, candidate])
);
const immediateProofPaths = immediateProofReport.proof_paths;
const candidateIds = [...new Set(paths.map(path => path.id))];
const candidateCoverage = candidateIds.map(id => {
  const baselineSet = new Set(
    baselineFingerprintCandidates.get(id).paths.flatMap(path => path.fingerprints)
  );
  const immediateSet = new Set(
    immediateProofPaths.filter(path => path.id === id).flatMap(path => path.fingerprints)
  );
  const delayedSet = new Set(proofPaths.filter(path => path.id === id).flatMap(path => path.fingerprints));
  const priorTwoPolicy = new Set([...baselineSet, ...immediateSet]);
  const newDelayed = [...delayedSet].filter(fingerprint => !priorTwoPolicy.has(fingerprint));
  const threePolicy = new Set([...priorTwoPolicy, ...delayedSet]);
  return {
    id,
    delayed_state_path_checks: proofPaths
      .filter(path => path.id === id)
      .reduce((sum, path) => sum + path.checks_completed, 0),
    baseline_distinct_fingerprints: baselineSet.size,
    immediate_distinct_fingerprints: immediateSet.size,
    delayed_distinct_fingerprints: delayedSet.size,
    prior_two_policy_fingerprints: priorTwoPolicy.size,
    new_delayed_fingerprints: newDelayed.length,
    three_policy_fingerprints: threePolicy.size,
    three_policy_digest_sha256: digest([...threePolicy])
  };
});

const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)];
};
const candidateSummary = candidateIds.map(id => {
  const candidatePaths = paths.filter(path => path.id === id);
  const delayedDepths = candidatePaths.map(path => path.delayed[25].largest_patch);
  const portfolioDepths = candidatePaths.map(path => Math.max(
    path.baseline.largest_patch,
    path.delayed[25].largest_patch
  ));
  return {
    id,
    delayed_25_robust_largest_patch: Math.min(...delayedDepths),
    delayed_25_median_largest_patch: median(delayedDepths),
    delayed_25_best_largest_patch: Math.max(...delayedDepths),
    delayed_25_target_hits: delayedDepths.filter(depth => depth >= baseline.configuration.target).length,
    baseline_delayed_portfolio_robust_largest_patch: Math.min(...portfolioDepths),
    baseline_delayed_portfolio_median_largest_patch: median(portfolioDepths),
    baseline_delayed_portfolio_best_largest_patch: Math.max(...portfolioDepths),
    baseline_delayed_portfolio_target_hits:
      portfolioDepths.filter(depth => depth >= baseline.configuration.target).length
  };
});

const thresholdSummary = [...thresholds.keys()].map(threshold => {
  const thresholdPaths = paths.map(path => ({
    baseline: path.baseline.largest_patch,
    immediate: path.immediate.largest_patch,
    delayed: path.delayed[threshold].largest_patch
  }));
  return {
    activation_failure_states: threshold,
    better_than_immediate: thresholdPaths.filter(path => path.delayed > path.immediate).length,
    equal_to_immediate: thresholdPaths.filter(path => path.delayed === path.immediate).length,
    worse_than_immediate: thresholdPaths.filter(path => path.delayed < path.immediate).length,
    better_than_baseline: thresholdPaths.filter(path => path.delayed > path.baseline).length,
    equal_to_baseline: thresholdPaths.filter(path => path.delayed === path.baseline).length,
    worse_than_baseline: thresholdPaths.filter(path => path.delayed < path.baseline).length,
    target_hits: thresholdPaths.filter(path => path.delayed >= baseline.configuration.target).length
  };
});
assert.deepEqual(
  thresholdSummary.find(summary => summary.activation_failure_states === 25),
  {
    activation_failure_states: 25,
    better_than_immediate: 2,
    equal_to_immediate: 10,
    worse_than_immediate: 0,
    better_than_baseline: 6,
    equal_to_baseline: 1,
    worse_than_baseline: 5,
    target_hits: 2
  }
);

const sumCoverage = field => candidateCoverage.reduce((sum, candidate) => sum + candidate[field], 0);
const targetProofPaths = proofPaths.filter(path => path.largest_patch >= baseline.configuration.target);
assert.ok(targetProofPaths.every(path => path.target_check_completed && !path.target_certificate_found));
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  benchmark_schema_version: baseline.schemaVersion,
  prior_two_policy_report: args.get("immediate-proof-report"),
  protocol: {
    witness_accounting: "largest_patch and witness_hash identify the last captured placement snapshot; max_live_tiles retains any transient uncaptured engine peak",
    baseline: baseline.configuration,
    immediate_nogood: {
      ...immediate.configuration,
      geometricNogoodActivationFailures: immediate.configuration.geometricNogoodActivationFailures ?? 0
    },
    delayed_25_exact_screen: delayedProof.configuration,
    activation_sweep_failure_states: [...thresholds.keys()]
  },
  paths,
  threshold_summary: thresholdSummary,
  proof_paths: proofPaths,
  candidate_summary: candidateSummary,
  candidate_coverage: candidateCoverage,
  summary: {
    candidates: candidateIds.length,
    paths_per_policy: paths.length,
    delayed_25_better_than_immediate: paths.filter(path => path.immediate_to_delayed_25_patch_delta > 0).length,
    delayed_25_equal_to_immediate: paths.filter(path => path.immediate_to_delayed_25_patch_delta === 0).length,
    delayed_25_worse_than_immediate: paths.filter(path => path.immediate_to_delayed_25_patch_delta < 0).length,
    delayed_25_target_hits: targetProofPaths.length,
    delayed_25_nogood_clauses: paths.reduce((sum, path) => sum + path.delayed[25].nogood_clauses, 0),
    delayed_25_nogood_prunes: paths.reduce((sum, path) => sum + path.delayed[25].nogood_prunes, 0),
    delayed_checkpoint_checks_completed: proofPaths.reduce((sum, path) => sum + path.checks_completed, 0),
    delayed_checkpoint_checks_timed_out: proofPaths.reduce((sum, path) => sum + path.checks_timed_out, 0),
    delayed_periodic_certificates_found: proofPaths.filter(path => path.certificate_found).length,
    delayed_distinct_fingerprints: sumCoverage("delayed_distinct_fingerprints"),
    prior_two_policy_fingerprints: sumCoverage("prior_two_policy_fingerprints"),
    new_delayed_fingerprints: sumCoverage("new_delayed_fingerprints"),
    three_policy_fingerprints: sumCoverage("three_policy_fingerprints"),
    three_policy_vs_baseline_multiplier:
      sumCoverage("three_policy_fingerprints") / sumCoverage("baseline_distinct_fingerprints"),
    policy_decision: "replace_immediate_nogood_lane_with_delayed_25"
  },
  interpretation: [
    "A fixed 250+250 baseline/nogood restart split did not beat the 500-node baseline on any sampled path, so fixed-budget restarts are not adopted.",
    "Learning nogoods from the start but delaying their application until 25 failed states weakly dominates immediate application on all 12 paths: two deepen and ten tie.",
    "The delayed policy reaches two independently hashed 40-tile 10_45033 witnesses; both target-patch quotient checks completed without a certificate.",
    "The delayed exact screen adds 199 rigid-motion patch geometries beyond the published baseline-plus-immediate union, bringing the three-policy checked union to 2,073.",
    "All results remain bounded finite-patch evidence; they prove neither non-tiling nor aperiodicity."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
