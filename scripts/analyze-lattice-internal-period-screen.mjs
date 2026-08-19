#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
for (const name of ["rank-aware", "rank-aware-proof", "control", "legacy-targets", "output"]) {
  assert.ok(args.get(name), `--${name}=<report.json> is required`);
}
const readJson = async path => JSON.parse(await readFile(path, "utf8"));
const readMany = async value => Promise.all(value.split(",").filter(Boolean).map(readJson));
const [rankReports, rankProof, control, legacyReports] = await Promise.all([
  readMany(args.get("rank-aware")),
  readJson(args.get("rank-aware-proof")),
  readJson(args.get("control")),
  readMany(args.get("legacy-targets"))
]);
assert.ok(rankReports.every(report => report.schemaVersion === 18));
assert.equal(rankProof.schemaVersion, 18);
assert.equal(control.schemaVersion, 18);
const candidateIds = ["10_16113", "10_45026", "10_45033", "9_11683"];
const rankRows = rankReports.flatMap(report => report.rows).sort((left, right) =>
  candidateIds.indexOf(left.case) - candidateIds.indexOf(right.case) || left.seed - right.seed
);
assert.equal(rankRows.length, 32);
assert.deepEqual([...new Set(rankRows.map(row => row.case))], candidateIds);
assert.ok(rankRows.every(row => row.witnessGrowthAxisRank === 3));
const median = values => values.slice().sort((left, right) => left - right)[Math.floor(values.length / 2)];
const compactPath = row => ({
  id: row.case,
  seed: row.seed,
  largest_patch: row.largestPatch,
  witness_hash: row.witnessHash,
  geometric_axis_rank: row.witnessGrowthAxisRank,
  repeated_translation_rank: row.witnessPeriodicTranslationRank,
  growth_spans: row.witnessGrowthSpans,
  growth_isotropy: row.witnessGrowthIsotropy,
  visited_nodes: row.visitedNodes,
  backtracks: row.backtracks,
  elapsed_ms: row.elapsedMs,
  termination_reason: row.terminationReason
});
const candidateSummary = candidateIds.map(id => {
  const rows = rankRows.filter(row => row.case === id);
  return {
    id,
    paths: rows.length,
    robust_largest_patch: Math.min(...rows.map(row => row.largestPatch)),
    median_largest_patch: median(rows.map(row => row.largestPatch)),
    best_largest_patch: Math.max(...rows.map(row => row.largestPatch)),
    target_hits: rows.filter(row => row.largestPatch >= 60).length,
    geometric_rank_3_paths: rows.filter(row => row.witnessGrowthAxisRank === 3).length,
    repeated_translation_rank_3_paths:
      rows.filter(row => row.witnessPeriodicTranslationRank === 3).length,
    time_limited_paths: rows.filter(row => row.terminationReason === "time_limit").length
  };
});
const proofRow = rankProof.rows[0];
assert.equal(proofRow.case, "10_16113");
assert.equal(proofRow.seed, 6);
assert.equal(proofRow.largestPatch, 60);
assert.equal(proofRow.genericPeriodicCertificateTargetCompleted, true);
assert.equal(proofRow.genericPeriodicCertificateTargetTimedOut, false);
assert.equal(proofRow.genericPeriodicCertificateTargetFound, false);
assert.equal(proofRow.genericPeriodicInternalMotifAttempted, true);
assert.equal(proofRow.genericPeriodicInternalMotifFound, false);
const compactExactCheck = row => ({
  id: row.case,
  seed: row.seed,
  patch_size: row.largestPatch,
  witness_hash: row.witnessHash,
  geometric_axis_rank: row.witnessGrowthAxisRank,
  repeated_translation_rank: row.witnessPeriodicTranslationRank,
  growth_spans: row.witnessGrowthSpans,
  growth_isotropy: row.witnessGrowthIsotropy,
  candidate_translation_vectors: row.genericPeriodicInternalMotifVectorCount,
  candidate_bases_tested: row.genericPeriodicInternalMotifBasesTested,
  maximum_translation_support: row.genericPeriodicInternalMotifMaxTranslationSupport,
  top_translations: row.genericPeriodicInternalMotifTopTranslations,
  whole_patch_or_internal_certificate_found: row.genericPeriodicCertificateTargetFound,
  check_completed: row.genericPeriodicCertificateTargetCompleted,
  check_timed_out: row.genericPeriodicCertificateTargetTimedOut
});
const controlRow = control.rows[0];
assert.equal(controlRow.case, "10_24775");
assert.equal(controlRow.certified, true);
assert.equal(controlRow.certificatePatchSize, 3);
assert.equal(controlRow.genericPeriodicInternalMotifFound, true);
const legacyTargetRows = legacyReports.flatMap(report => report.rows)
  .filter(row => row.largestPatch >= 60)
  .sort((left, right) => left.case.localeCompare(right.case) || left.seed - right.seed);
assert.equal(legacyTargetRows.length, 7);
assert.ok(legacyTargetRows.every(row => row.genericPeriodicInternalMotifAttempted));
assert.ok(legacyTargetRows.every(row => !row.genericPeriodicInternalMotifFound));
const legacyChecks = legacyTargetRows.map(compactExactCheck);
const collinearChainChecks = legacyChecks.filter(check =>
  check.id === "10_45026" && check.maximum_translation_support >= 57
);
assert.equal(collinearChainChecks.length, 4);

const archive = {
  schema_version: 1,
  screen_date: "2026-08-19",
  benchmark_schema_versions: [17, 18],
  protocol: {
    candidates: candidateIds,
    seeds: [1, 2, 3, 4, 5, 6, 7, 8],
    target_tiles: 60,
    node_limit: 1000,
    time_limit_ms: 5000,
    move_order: "crystal",
    face_order: "mrv",
    generation_band: false,
    exact_failure_memo: true,
    internal_period_vector_limit: 48,
    exact_check_time_limit_ms: 15000
  },
  focused_target_protocol: {
    id: "10_16113",
    seed: 6,
    target_tiles: 60,
    node_limit: 1000,
    search_time_limit_ms: 30000,
    exact_check_time_limit_ms: 15000
  },
  method: {
    search_change: "prioritize gains in the rank of repeated same-orientation translation vectors before ordinary crystal continuation scores",
    translation_diagnostic: "rank candidate vectors by the number of same-frame placement pairs realizing each translation",
    exact_internal_motif_check: "enumerate independent candidate-vector bases, reduce the observed patch to placement cosets, and require an exact face pairing with motif volume equal to lattice covolume",
    negative_result_scope: "excludes exact quotients exhibited by the checked finite witness within the 48-vector candidate cap; it is not a proof that the tile has no periodic tiling"
  },
  legacy_crystal_target_checks: {
    checked_witnesses: legacyChecks.length,
    certificates_found: legacyChecks.filter(check => check.whole_patch_or_internal_certificate_found).length,
    highly_collinear_10_45026_witnesses: collinearChainChecks.length,
    observation: "all four 10_45026 target paths repeated 57 of 60 placements along one translation direction",
    checks: legacyChecks
  },
  repeated_translation_rank_screen: {
    paths: rankRows.length,
    geometric_rank_3_paths: rankRows.filter(row => row.witnessGrowthAxisRank === 3).length,
    repeated_translation_rank_3_paths:
      rankRows.filter(row => row.witnessPeriodicTranslationRank === 3).length,
    target_hits: rankRows.filter(row => row.largestPatch >= 60).length,
    candidate_summary: candidateSummary,
    paths_detail: rankRows.map(compactPath)
  },
  exact_target_check: compactExactCheck(proofRow),
  positive_control: {
    ...compactExactCheck(controlRow),
    certificate_kind: controlRow.certificateKind,
    certificate_patch_size: controlRow.certificatePatchSize,
    period_vectors: controlRow.periodVectors
  },
  decision: "replace the crystal lane's affine-position rank gate with repeated-translation rank; retain it as a complementary bounded search and report dimensional evidence separately from tile count"
};
await writeFile(args.get("output"), `${JSON.stringify(archive, null, 2)}\n`);
process.stdout.write(`${JSON.stringify({
  output: args.get("output"),
  candidate_summary: candidateSummary,
  exact_target_check: archive.exact_target_check,
  positive_control: archive.positive_control,
  decision: archive.decision
}, null, 2)}\n`);
