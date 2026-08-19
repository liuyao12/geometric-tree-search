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
const policyNames = ["baseline", "immediate", "delayed"];
const required = [
  ...policyNames.flatMap(policy => [`${policy}-search`, `${policy}-proof`]),
  "prior-baseline-report",
  "prior-immediate-report",
  "prior-delayed-report"
];
for (const name of required) assert.ok(args.get(name), `--${name}=<report.json> is required`);
const readJson = async name => JSON.parse(await readFile(args.get(name), "utf8"));
const loaded = Object.fromEntries(await Promise.all(required.map(async name => [name, await readJson(name)])));
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
const searchReports = Object.fromEntries(policyNames.map(policy => [
  policy,
  normalizeCapturedWitnesses(loaded[`${policy}-search`])
]));
const proofReports = Object.fromEntries(policyNames.map(policy => [
  policy,
  normalizeCapturedWitnesses(loaded[`${policy}-proof`])
]));
const priorBaseline = loaded["prior-baseline-report"];
const priorImmediate = loaded["prior-immediate-report"];
const priorDelayed = loaded["prior-delayed-report"];

const schemas = new Set([
  ...Object.values(searchReports),
  ...Object.values(proofReports)
].map(report => report.schemaVersion));
assert.deepEqual([...schemas], [15]);
assert.equal(searchReports.baseline.configuration.geometricNogood, false);
assert.equal(searchReports.immediate.configuration.geometricNogood, true);
assert.equal(searchReports.immediate.configuration.geometricNogoodActivationFailures, 0);
assert.equal(searchReports.delayed.configuration.geometricNogood, true);
assert.equal(searchReports.delayed.configuration.geometricNogoodActivationFailures, 25);
for (const policy of policyNames) {
  assert.deepEqual(searchReports[policy].configuration.seeds, [4, 5, 6, 7, 8]);
  assert.deepEqual(proofReports[policy].configuration.seeds, [4, 5, 6, 7, 8]);
  assert.equal(searchReports[policy].rows.length, 20);
  assert.equal(proofReports[policy].rows.length, 20);
}

const without = (object, omitted) => Object.fromEntries(
  Object.entries(object).filter(([key]) => !omitted.includes(key))
);
const variantKeys = ["geometricNogood", "geometricNogoodActivationFailures"];
for (const policy of ["immediate", "delayed"]) {
  assert.deepEqual(
    without(searchReports[policy].configuration, variantKeys),
    without(searchReports.baseline.configuration, variantKeys),
    `${policy} search may differ from baseline only in its nogood policy`
  );
}
const exactKeys = [
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
for (const policy of policyNames) {
  assert.deepEqual(
    without(proofReports[policy].configuration, exactKeys),
    without(searchReports[policy].configuration, exactKeys),
    `${policy} proof replay may differ only in exact-checkpoint settings`
  );
}

const keyOf = row => `${row.case}:${row.seed}`;
const rowsByKey = report => new Map(report.rows.map(row => [keyOf(row), row]));
const searchRows = Object.fromEntries(policyNames.map(policy => [policy, rowsByKey(searchReports[policy])]));
const proofRows = Object.fromEntries(policyNames.map(policy => [policy, rowsByKey(proofReports[policy])]));
const pathKeys = [...searchRows.baseline.keys()];
for (const policy of policyNames) {
  assert.deepEqual([...searchRows[policy].keys()], pathKeys);
  assert.deepEqual([...proofRows[policy].keys()], pathKeys);
}
const pathIdentity = row => [
  row.case,
  row.seed,
  row.largestPatch,
  row.witnessHash,
  row.visitedNodes,
  row.backtracks,
  row.terminationReason
];
for (const policy of policyNames) {
  for (const key of pathKeys) {
    assert.deepEqual(
      pathIdentity(proofRows[policy].get(key)),
      pathIdentity(searchRows[policy].get(key)),
      `${policy}/${key}: exact checking changed the bounded search path`
    );
  }
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
  growth_milestones: compactMilestones(row)
});
const searchPaths = pathKeys.map(key => ({
  id: searchRows.baseline.get(key).case,
  seed: searchRows.baseline.get(key).seed,
  baseline: compactOutcome(searchRows.baseline.get(key)),
  immediate: compactOutcome(searchRows.immediate.get(key)),
  delayed_25: compactOutcome(searchRows.delayed.get(key)),
  delayed_vs_immediate_patch_delta:
    searchRows.delayed.get(key).largestPatch - searchRows.immediate.get(key).largestPatch,
  delayed_vs_baseline_patch_delta:
    searchRows.delayed.get(key).largestPatch - searchRows.baseline.get(key).largestPatch
}));

const digest = values => createHash("sha256").update(values.slice().sort().join("\n")).digest("hex");
const proofPaths = [];
for (const policy of policyNames) {
  for (const key of pathKeys) {
    const row = proofRows[policy].get(key);
    assert.equal(row.genericPeriodicCertificateChecksAttempted, row.genericPeriodicCertificateChecksCompleted);
    assert.equal(row.genericPeriodicCertificateChecksTimedOut, 0);
    assert.equal(row.genericPeriodicCertificateFound, false);
    const fingerprints = row.genericPeriodicCertificateCheckFingerprints;
    assert.equal(new Set(fingerprints).size, fingerprints.length);
    proofPaths.push({
      policy,
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
    });
  }
}

const candidateIds = [...new Set(searchPaths.map(path => path.id))];
const priorBaselineCandidates = new Map(priorBaseline.candidates.map(candidate => [candidate.id, candidate]));
const priorImmediatePaths = priorImmediate.proof_paths;
const priorDelayedPaths = priorDelayed.proof_paths;
const candidateCoverage = candidateIds.map(id => {
  const priorSet = new Set([
    ...priorBaselineCandidates.get(id).paths.flatMap(path => path.fingerprints),
    ...priorImmediatePaths.filter(path => path.id === id).flatMap(path => path.fingerprints),
    ...priorDelayedPaths.filter(path => path.id === id).flatMap(path => path.fingerprints)
  ]);
  const holdoutSets = Object.fromEntries(policyNames.map(policy => [
    policy,
    new Set(proofPaths
      .filter(path => path.policy === policy && path.id === id)
      .flatMap(path => path.fingerprints))
  ]));
  const holdoutUnion = new Set(policyNames.flatMap(policy => [...holdoutSets[policy]]));
  const expandedUnion = new Set([...priorSet, ...holdoutUnion]);
  return {
    id,
    holdout_checks_completed: proofPaths
      .filter(path => path.id === id)
      .reduce((sum, path) => sum + path.checks_completed, 0),
    prior_three_policy_fingerprints: priorSet.size,
    holdout_baseline_fingerprints: holdoutSets.baseline.size,
    holdout_immediate_fingerprints: holdoutSets.immediate.size,
    holdout_delayed_fingerprints: holdoutSets.delayed.size,
    holdout_union_fingerprints: holdoutUnion.size,
    new_holdout_fingerprints: [...holdoutUnion].filter(fingerprint => !priorSet.has(fingerprint)).length,
    expanded_eight_seed_fingerprints: expandedUnion.size,
    expanded_digest_sha256: digest([...expandedUnion])
  };
});

const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)];
};
const candidateSummary = candidateIds.map(id => {
  const paths = searchPaths.filter(path => path.id === id);
  const delayedDepths = paths.map(path => path.delayed_25.largest_patch);
  const portfolioDepths = paths.map(path => Math.max(path.baseline.largest_patch, path.delayed_25.largest_patch));
  return {
    id,
    holdout_delayed_robust_largest_patch: Math.min(...delayedDepths),
    holdout_delayed_median_largest_patch: median(delayedDepths),
    holdout_delayed_best_largest_patch: Math.max(...delayedDepths),
    holdout_delayed_target_hits: delayedDepths.filter(depth => depth >= 40).length,
    holdout_baseline_delayed_portfolio_robust_largest_patch: Math.min(...portfolioDepths),
    holdout_baseline_delayed_portfolio_median_largest_patch: median(portfolioDepths),
    holdout_baseline_delayed_portfolio_best_largest_patch: Math.max(...portfolioDepths),
    holdout_baseline_delayed_portfolio_target_hits: portfolioDepths.filter(depth => depth >= 40).length
  };
});

const comparison = paths => ({
  delayed_better_than_immediate: paths.filter(path => path.delayed_25.largest_patch > path.immediate.largest_patch).length,
  delayed_equal_to_immediate: paths.filter(path => path.delayed_25.largest_patch === path.immediate.largest_patch).length,
  delayed_worse_than_immediate: paths.filter(path => path.delayed_25.largest_patch < path.immediate.largest_patch).length,
  delayed_better_than_baseline: paths.filter(path => path.delayed_25.largest_patch > path.baseline.largest_patch).length,
  delayed_equal_to_baseline: paths.filter(path => path.delayed_25.largest_patch === path.baseline.largest_patch).length,
  delayed_worse_than_baseline: paths.filter(path => path.delayed_25.largest_patch < path.baseline.largest_patch).length,
  baseline_target_hits: paths.filter(path => path.baseline.largest_patch >= 40).length,
  immediate_target_hits: paths.filter(path => path.immediate.largest_patch >= 40).length,
  delayed_target_hits: paths.filter(path => path.delayed_25.largest_patch >= 40).length
});
const trainingPaths = priorDelayed.paths.map(path => ({
  baseline: path.baseline,
  immediate: path.immediate,
  delayed_25: path.delayed[25]
}));
const holdoutComparison = comparison(searchPaths);
const trainingComparison = comparison(trainingPaths);
const combinedComparison = Object.fromEntries(
  Object.keys(holdoutComparison).map(key => [key, holdoutComparison[key] + trainingComparison[key]])
);
assert.deepEqual(holdoutComparison, {
  delayed_better_than_immediate: 5,
  delayed_equal_to_immediate: 14,
  delayed_worse_than_immediate: 1,
  delayed_better_than_baseline: 6,
  delayed_equal_to_baseline: 3,
  delayed_worse_than_baseline: 11,
  baseline_target_hits: 1,
  immediate_target_hits: 1,
  delayed_target_hits: 2
});

const targetChecks = proofPaths.filter(path => path.target_check_completed);
assert.ok(targetChecks.every(path => !path.target_certificate_found));
const sumCoverage = field => candidateCoverage.reduce((sum, candidate) => sum + candidate[field], 0);
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  benchmark_schema_version: 15,
  prior_three_policy_report: args.get("prior-delayed-report"),
  protocol: {
    witness_accounting: "largest_patch and witness_hash identify the last captured placement snapshot; max_live_tiles retains any transient uncaptured engine peak",
    baseline: searchReports.baseline.configuration,
    immediate: searchReports.immediate.configuration,
    delayed_25: searchReports.delayed.configuration,
    exact_screen: proofReports.delayed.configuration
  },
  search_paths: searchPaths,
  proof_paths: proofPaths,
  candidate_summary: candidateSummary,
  candidate_coverage: candidateCoverage,
  generalization: {
    training_seeds_1_through_3: trainingComparison,
    holdout_seeds_4_through_8: holdoutComparison,
    combined_seeds_1_through_8: combinedComparison
  },
  summary: {
    candidates: candidateIds.length,
    holdout_seeds: [4, 5, 6, 7, 8],
    paths_per_policy: searchPaths.length,
    total_policy_paths: proofPaths.length,
    exact_checks_completed: proofPaths.reduce((sum, path) => sum + path.checks_completed, 0),
    exact_checks_timed_out: proofPaths.reduce((sum, path) => sum + path.checks_timed_out, 0),
    periodic_certificates_found: proofPaths.filter(path => path.certificate_found).length,
    completed_target_patch_checks: targetChecks.length,
    distinct_target_witnesses: new Set(targetChecks.map(path => path.witness_hash)).size,
    prior_three_policy_fingerprints: sumCoverage("prior_three_policy_fingerprints"),
    holdout_union_fingerprints: sumCoverage("holdout_union_fingerprints"),
    new_holdout_fingerprints: sumCoverage("new_holdout_fingerprints"),
    expanded_eight_seed_fingerprints: sumCoverage("expanded_eight_seed_fingerprints"),
    expanded_vs_training_multiplier:
      sumCoverage("expanded_eight_seed_fingerprints") / sumCoverage("prior_three_policy_fingerprints"),
    policy_decision: "retain_delayed_25_as_complementary_holdout_supported_lane"
  },
  interpretation: [
    "On five unseen seeds, delayed-25 improves five immediate-nogood paths, ties fourteen, and worsens one; the three-seed dominance claim does not generalize literally.",
    "Delayed-25 nevertheless reaches two 40-tile targets on holdout seeds versus one for immediate nogoods and one for baseline, so it remains a useful complementary lane.",
    "All 5,540 holdout quotient checks completed without timeout or periodic certificate, including both distinct 40-tile witness hashes.",
    "The holdout adds 2,758 rigid-motion patch geometries beyond the prior 2,073, expanding eight-seed three-policy coverage to 4,831.",
    "These are bounded finite-patch and quotient-screen results, not proofs of non-tiling or aperiodicity."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
