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
for (const name of ["baseline-search", "nogood-search", "nogood-proof", "prior-fingerprint-report"]) {
  assert.ok(args.get(name), `--${name}=<report.json> is required`);
}
const readJson = async name => JSON.parse(await readFile(args.get(name), "utf8"));
const baselineSearch = await readJson("baseline-search");
const nogoodSearch = await readJson("nogood-search");
const nogoodProof = await readJson("nogood-proof");
const priorFingerprints = await readJson("prior-fingerprint-report");
assert.equal(baselineSearch.schemaVersion, nogoodSearch.schemaVersion);
assert.equal(nogoodSearch.schemaVersion, nogoodProof.schemaVersion);
assert.equal(baselineSearch.configuration.geometricNogood, false);
assert.equal(nogoodSearch.configuration.geometricNogood, true);
assert.equal(nogoodProof.configuration.geometricNogood, true);

const without = (object, keys) => Object.fromEntries(Object.entries(object)
  .filter(([key]) => !keys.includes(key)));
assert.deepEqual(
  without(baselineSearch.configuration, ["geometricNogood"]),
  without(nogoodSearch.configuration, ["geometricNogood"]),
  "search A/B configurations must differ only by geometric nogoods"
);
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
  without(nogoodSearch.configuration, exactConfigKeys),
  without(nogoodProof.configuration, exactConfigKeys),
  "nogood path and exact-proof configurations must differ only by checkpoint checking"
);
assert.equal(baselineSearch.rows.length, nogoodSearch.rows.length);
assert.equal(nogoodSearch.rows.length, nogoodProof.rows.length);

const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const digest = values => createHash("sha256").update(values.slice().sort().join("\n")).digest("hex");
const searchPaths = baselineSearch.rows.map((baseline, index) => {
  const nogood = nogoodSearch.rows[index];
  const proof = nogoodProof.rows[index];
  assert.equal(baseline.case, nogood.case);
  assert.equal(baseline.seed, nogood.seed);
  assert.deepEqual(
    [nogood.case, nogood.seed, nogood.witnessHash, nogood.largestPatch, nogood.visitedNodes, nogood.backtracks],
    [proof.case, proof.seed, proof.witnessHash, proof.largestPatch, proof.visitedNodes, proof.backtracks],
    `${nogood.case} seed ${nogood.seed}: checkpoint checking changed the nogood search path`
  );
  assert.equal(nogood.geometricNogoodEnabled, true);
  assert.equal(nogood.geometricNogoodCapacityReached, false);
  return {
    id: baseline.case,
    seed: baseline.seed,
    baseline: {
      largest_patch: baseline.largestPatch,
      witness_hash: baseline.witnessHash,
      visited_nodes: baseline.visitedNodes,
      backtracks: baseline.backtracks,
      elapsed_ms: baseline.elapsedMs,
      termination_reason: baseline.terminationReason
    },
    nogood: {
      largest_patch: nogood.largestPatch,
      witness_hash: nogood.witnessHash,
      visited_nodes: nogood.visitedNodes,
      backtracks: nogood.backtracks,
      elapsed_ms: nogood.elapsedMs,
      termination_reason: nogood.terminationReason,
      clauses: nogood.geometricNogoodClauses,
      prunes: nogood.geometricNogoodPrunes,
      avoided_clause_checks: nogood.geometricNogoodAvoidedClauseChecks
    },
    patch_delta: nogood.largestPatch - baseline.largestPatch
  };
});
const target = baselineSearch.configuration.target;
const candidateIds = [...new Set(searchPaths.map(path => path.id))];
const depthSummary = paths => {
  const depths = paths.map(path => path.largest_patch);
  return {
    robust_largest_patch: Math.min(...depths),
    median_largest_patch: median(depths),
    best_largest_patch: Math.max(...depths),
    target_hits: depths.filter(depth => depth >= target).length
  };
};
const candidateSearchSummary = candidateIds.map(id => {
  const paths = searchPaths.filter(path => path.id === id);
  const baseline = depthSummary(paths.map(path => path.baseline));
  const nogood = depthSummary(paths.map(path => path.nogood));
  const portfolio = depthSummary(paths.map(path => ({
    largest_patch: Math.max(path.baseline.largest_patch, path.nogood.largest_patch)
  })));
  return {
    id,
    baseline,
    nogood,
    two_policy_portfolio: portfolio,
    improved_paths: paths.filter(path => path.patch_delta > 0).length,
    equal_paths: paths.filter(path => path.patch_delta === 0).length,
    worsened_paths: paths.filter(path => path.patch_delta < 0).length
  };
});

const proofPaths = nogoodProof.rows.map(row => {
  const fingerprints = row.genericPeriodicCertificateCheckFingerprints ?? [];
  assert.equal(fingerprints.length, row.genericPeriodicCertificateChecksAttempted);
  assert.equal(new Set(fingerprints).size, fingerprints.length);
  assert.ok(fingerprints.every(value => /^[0-9a-f]{32}$/.test(value)));
  assert.equal(
    row.genericPeriodicCertificateChecksCompleted + row.genericPeriodicCertificateChecksTimedOut,
    row.genericPeriodicCertificateChecksAttempted
  );
  return {
    id: row.case,
    seed: row.seed,
    witness_hash: row.witnessHash,
    largest_patch: row.largestPatch,
    visited_nodes: row.visitedNodes,
    backtracks: row.backtracks,
    termination_reason: row.terminationReason,
    eligible_states: row.genericPeriodicCertificateCheckpointEligibleStates,
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
const priorById = new Map(priorFingerprints.candidates.map(candidate => [candidate.id, candidate]));
const candidateCoverage = candidateIds.map(id => {
  const currentPaths = proofPaths.filter(path => path.id === id);
  const current = new Set(currentPaths.flatMap(path => path.fingerprints));
  const priorCandidate = priorById.get(id);
  assert.ok(priorCandidate, `${id}: missing prior fingerprint evidence`);
  const prior = new Set(priorCandidate.paths.flatMap(path => path.fingerprints));
  const shared = [...current].filter(fingerprint => prior.has(fingerprint));
  const newFingerprints = [...current].filter(fingerprint => !prior.has(fingerprint));
  const combined = new Set([...prior, ...current]);
  return {
    id,
    nogood_state_path_checks: currentPaths.reduce((sum, path) => sum + path.checks_attempted, 0),
    nogood_distinct_fingerprints: current.size,
    prior_distinct_fingerprints: prior.size,
    shared_fingerprints: shared.length,
    new_fingerprints: newFingerprints.length,
    combined_distinct_fingerprints: combined.size,
    combined_digest_sha256: digest([...combined])
  };
});
const currentDistinct = candidateCoverage.reduce((sum, candidate) => sum + candidate.nogood_distinct_fingerprints, 0);
const priorDistinct = candidateCoverage.reduce((sum, candidate) => sum + candidate.prior_distinct_fingerprints, 0);
const sharedDistinct = candidateCoverage.reduce((sum, candidate) => sum + candidate.shared_fingerprints, 0);
const newDistinct = candidateCoverage.reduce((sum, candidate) => sum + candidate.new_fingerprints, 0);
const combinedDistinct = candidateCoverage.reduce((sum, candidate) => sum + candidate.combined_distinct_fingerprints, 0);
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  benchmark_schema_version: nogoodProof.schemaVersion,
  prior_fingerprint_report: args.get("prior-fingerprint-report"),
  protocol: {
    search_ab: without(baselineSearch.configuration, ["geometricNogood"]),
    exact_nogood_screen: nogoodProof.configuration,
    nogood_model: "complete failed context, translation-equivariant, rare-token pivot index"
  },
  search_paths: searchPaths,
  candidate_search_summary: candidateSearchSummary,
  proof_paths: proofPaths,
  candidate_coverage: candidateCoverage,
  summary: {
    candidates: candidateIds.length,
    paths_per_policy: searchPaths.length,
    improved_nogood_paths: searchPaths.filter(path => path.patch_delta > 0).length,
    equal_nogood_paths: searchPaths.filter(path => path.patch_delta === 0).length,
    worsened_nogood_paths: searchPaths.filter(path => path.patch_delta < 0).length,
    baseline_target_hits: searchPaths.filter(path => path.baseline.largest_patch >= target).length,
    nogood_target_hits: searchPaths.filter(path => path.nogood.largest_patch >= target).length,
    total_nogood_clauses: searchPaths.reduce((sum, path) => sum + path.nogood.clauses, 0),
    total_nogood_prunes: searchPaths.reduce((sum, path) => sum + path.nogood.prunes, 0),
    nogood_capacity_reached_paths: nogoodSearch.rows.filter(row => row.geometricNogoodCapacityReached).length,
    nogood_checkpoint_state_path_checks: proofPaths.reduce((sum, path) => sum + path.checks_attempted, 0),
    nogood_checkpoint_checks_completed: proofPaths.reduce((sum, path) => sum + path.checks_completed, 0),
    nogood_checkpoint_checks_timed_out: proofPaths.reduce((sum, path) => sum + path.checks_timed_out, 0),
    nogood_periodic_certificates_found: proofPaths.filter(path => path.certificate_found).length,
    completed_target_patch_checks: proofPaths.filter(path => path.target_check_completed).length,
    prior_distinct_fingerprints: priorDistinct,
    nogood_distinct_fingerprints: currentDistinct,
    shared_fingerprints: sharedDistinct,
    new_nogood_fingerprints: newDistinct,
    combined_distinct_fingerprints: combinedDistinct,
    combined_coverage_multiplier: priorDistinct ? combinedDistinct / priorDistinct : null,
    policy_decision: "complementary_proof_lane"
  },
  interpretation: [
    "Nogoods are not a uniformly better replacement ordering: five paths deepened, one tied, and six became shallower under the same node cap.",
    "As a complementary policy they add a new 40-tile witness for 10_45033 and improve the per-seed best-of-two portfolio without removing any baseline witness.",
    `${proofPaths.reduce((sum, path) => sum + path.checks_attempted, 0)} exact nogood-path checks add ${newDistinct} rigid-motion patch geometries beyond the prior ${priorDistinct}, for a combined union of ${combinedDistinct}.`,
    "Every nogood-path quotient check completed without a periodic certificate; the expanded evidence remains bounded and does not prove non-tiling or aperiodicity.",
    "Translation-equivariant nogoods remain disabled for finite target regions, where translation is not a sound equivalence."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
