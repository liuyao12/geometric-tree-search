#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const reportPath = new URL(
  "../data/lattice-polyhedron-global-extension-screen-2026-08-19.json",
  import.meta.url
);
const report = JSON.parse(await readFile(reportPath, "utf8"));
const candidateIds = ["10_16113", "10_45026", "10_45033", "9_11683"];
const rows = report.rows ?? [];

assert.equal(report.schemaVersion, 19);
assert.equal(report.configuration.connectedPatchEnumeration, true);
assert.equal(report.configuration.unbandedMoveOrder, "global");
assert.deepEqual(report.configuration.seeds, [1, 2, 3]);
assert.equal(report.configuration.target, 60);
assert.equal(rows.length, candidateIds.length * report.configuration.seeds.length);
assert.deepEqual([...new Set(rows.map(row => row.case))], candidateIds);
assert.ok(rows.every(row => row.connectedPatchEnumeration));
assert.ok(rows.every(row => row.largestPatch === 60 && row.resultKind === "patch_found"));
assert.ok(rows.every(row => row.visitedNodes === 60 && row.backtracks === 0));
assert.ok(rows.every(row => row.witnessGrowthAxisRank === 3));
assert.ok(rows.every(row => row.witnessPeriodicTranslationRank === 3));
assert.ok(rows.every(row => row.genericPeriodicCertificateChecksCompleted === 1));
assert.ok(rows.every(row => row.genericPeriodicCertificateChecksTimedOut === 0));
assert.ok(rows.every(row => !row.genericPeriodicCertificateFound));
assert.ok(rows.every(row => row.genericPeriodicInternalMotifAttempted));
assert.ok(rows.every(row => !row.genericPeriodicInternalMotifFound));

const candidateSummary = candidateIds.map(id => {
  const candidateRows = rows.filter(row => row.case === id);
  return {
    id,
    trials: candidateRows.length,
    target_hits: candidateRows.filter(row => row.largestPatch === 60).length,
    distinct_witnesses: new Set(candidateRows.map(row => row.witnessHash)).size,
    minimum_isotropy: Math.min(...candidateRows.map(row => row.witnessGrowthIsotropy)),
    maximum_live_candidates: Math.max(...candidateRows.map(row => row.connectedPatchMaxCandidates)),
    exact_target_checks: candidateRows.reduce(
      (sum, row) => sum + row.genericPeriodicCertificateChecksCompleted,
      0
    ),
    internal_period_bases_tested: candidateRows.reduce(
      (sum, row) => sum + row.genericPeriodicInternalMotifBasesTested,
      0
    ),
    periodic_certificates: candidateRows.filter(row => row.genericPeriodicCertificateFound).length
  };
});

const summary = {
  schema_version: 1,
  screen_date: "2026-08-19",
  correction: {
    prior_frontier_error:
      "A temporarily stranded frontier vertex was treated as a dead end and a currently unique vertex candidate was treated as forced.",
    prior_budget_error:
      "Displayed alternative IDs, including unvisited branches, were charged against the node budget.",
    corrected_search:
      "Enumerate every legal exposed-face extension and charge the node budget only when a placement is actually applied."
  },
  model: "connected face-to-face patches using proper cubic lattice orientations",
  target_tiles: report.configuration.target,
  trials: rows.length,
  target_hits: rows.filter(row => row.largestPatch === report.configuration.target).length,
  distinct_witnesses: new Set(rows.map(row => row.witnessHash)).size,
  rank_3_witnesses: rows.filter(row =>
    row.witnessGrowthAxisRank === 3 && row.witnessPeriodicTranslationRank === 3
  ).length,
  exact_target_checks: rows.reduce(
    (sum, row) => sum + row.genericPeriodicCertificateChecksCompleted,
    0
  ),
  exact_target_check_timeouts: rows.reduce(
    (sum, row) => sum + row.genericPeriodicCertificateChecksTimedOut,
    0
  ),
  internal_period_bases_tested: rows.reduce(
    (sum, row) => sum + row.genericPeriodicInternalMotifBasesTested,
    0
  ),
  periodic_certificates: rows.filter(row => row.genericPeriodicCertificateFound).length,
  candidate_summary: candidateSummary,
  conclusion:
    "All four candidates readily support large balanced 3D patches under the corrected search. None of the 12 checked 60-tile witnesses contains an exact periodic quotient within the configured internal-period screen; this is evidence, not an aperiodicity proof."
};

process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
