#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { polycubeCoronaRingCellKeys } from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = resolve(args.get("manifest")
  ?? `${repositoryRoot}/data/polycube-p10-052588-complete-radius3-exhaustion-2026-08-23.json`);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const failures = [];
const assert = (condition, message) => {
  if (!condition) failures.push(message);
};
const readArtifact = reference => {
  const path = resolve(repositoryRoot, reference.path);
  const bytes = readFileSync(path);
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  assert(sha256 === reference.sha256, `${reference.path}: SHA-256 mismatch`);
  return JSON.parse(bytes.toString("utf8"));
};

assert(manifest.kind === "polycube_complete_radius_exhaustion_audit", "unexpected manifest kind");
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === manifest.candidate);
assert(candidate, `unknown candidate ${manifest.candidate}`);
assert(manifest.model?.include_reflections === false, "proof model must explicitly exclude reflections");
assert(manifest.model?.fixed_root === true, "proof model must fix one root copy");
assert(manifest.model?.outer_radius === 3 && manifest.model?.continuation_radius === 4,
  "proof must connect radius three to radius four");

const prefix = readArtifact(manifest.count_cover.prefix.artifact);
const prefixCertificate = prefix.widened_bounded_exhaustion_through_46_copies;
assert(prefix.candidate === manifest.candidate, "prefix candidate mismatch");
assert(prefixCertificate?.maximum_outer_placements === manifest.count_cover.prefix.maximum,
  "prefix maximum mismatch");
assert(prefixCertificate?.seed_231_cache_miss?.z3_status === "unsat",
  "bounded prefix lacks an exact UNSAT result");
assert(prefixCertificate?.applied_clauses === manifest.count_cover.prefix.clauses,
  "bounded prefix clause count mismatch");
assert(prefixCertificate?.applied_cells === manifest.count_cover.prefix.cells,
  "bounded prefix cell count mismatch");

const exactCounts = [];
for (const component of manifest.count_cover.exact_components) {
  const report = readArtifact(component.artifact);
  assert(report.candidate === manifest.candidate, `${component.artifact.path}: candidate mismatch`);
  assert(report.result === "unsat", `${component.artifact.path}: result is not UNSAT`);
  assert(/^placement_cube_(cover|range|ranges)_exhausted$/.test(report.classification),
    `${component.artifact.path}: unexpected classification`);
  const counts = report.placement_counts ?? [report.placement_count];
  assert(counts.every(Number.isInteger), `${component.artifact.path}: invalid placement counts`);
  assert(JSON.stringify(counts) === JSON.stringify(component.counts),
    `${component.artifact.path}: manifest count mismatch`);
  const formula = report.shared_formula_shape ?? report.shared_formula;
  assert(formula?.applied_forbidden_clauses === component.clauses,
    `${component.artifact.path}: applied clause count mismatch`);
  assert(formula?.cell_coverability_constraints === component.cells,
    `${component.artifact.path}: applied cell count mismatch`);
  exactCounts.push(...counts);
  if (Array.isArray(report.covers)) {
    for (const cover of report.covers) {
      assert(cover.covered_anchor_placement_candidates === report.anchor_placement_candidates,
        `${component.artifact.path}: incomplete anchor cover at ${cover.placement_count}`);
      assert(cover.uncovered_anchor_placement_candidates === 0,
        `${component.artifact.path}: uncovered anchor branch at ${cover.placement_count}`);
      assert(cover.leaf_overlaps === 0,
        `${component.artifact.path}: overlapping anchor branches at ${cover.placement_count}`);
    }
  } else {
    assert(report.coverage_verification?.uncovered_anchor_placement_candidates === 0,
      `${component.artifact.path}: incomplete single-count anchor cover`);
    assert(report.coverage_verification?.leaf_overlaps === 0,
      `${component.artifact.path}: overlapping single-count anchor cover`);
  }
}
const expectedExactCounts = Array.from(
  { length: manifest.count_cover.tail.minimum - manifest.count_cover.prefix.maximum - 1 },
  (_, index) => manifest.count_cover.prefix.maximum + index + 1
);
assert(JSON.stringify(exactCounts) === JSON.stringify(expectedExactCounts),
  "exact-count components are not a contiguous bridge from prefix to tail");

const tail = readArtifact(manifest.count_cover.tail.artifact);
assert(tail.candidate === manifest.candidate, "tail candidate mismatch");
assert(tail.classification === "placement_cube_tail_exhausted" && tail.result === "unsat",
  "open-ended tail is not exhausted");
assert(tail.minimum_placement_count === manifest.count_cover.tail.minimum
  && tail.maximum_placement_count === null, "tail bounds mismatch");
assert(tail.open_ended_tail_exhausted === true, "tail is not marked open-ended");
assert(tail.shared_formula?.applied_forbidden_clauses === manifest.count_cover.tail.clauses,
  "tail applied clause count mismatch");
assert(tail.shared_formula?.cell_coverability_constraints === manifest.count_cover.tail.cells,
  "tail applied cell count mismatch");
assert(tail.covered_anchor_placement_candidates === tail.anchor_placement_candidates
  && tail.uncovered_anchor_placement_candidates === 0 && tail.leaf_overlaps === 0,
  "tail anchor partition is incomplete");

for (const condition of manifest.sound_necessary_conditions) {
  const clauses = readArtifact(condition.clauses);
  const cells = readArtifact(condition.cells);
  const replay = readArtifact(condition.clause_replay);
  assert(Array.isArray(clauses.clauses) && clauses.clauses.length === condition.clause_count,
    `${condition.id}: clause count mismatch`);
  assert(Array.isArray(cells.cells) && cells.cells.length === condition.cell_count,
    `${condition.id}: cell count mismatch`);
  assert(new Set(cells.cells.map(String)).size === condition.cell_count,
    `${condition.id}: cell report contains duplicates`);
  assert(replay.candidate === manifest.candidate && replay.layer === manifest.model.continuation_radius,
    `${condition.id}: clause replay model mismatch`);
  assert(replay.clause_report === condition.clauses.path,
    `${condition.id}: clause replay points at a different clause file`);
  assert(replay.classification === "verified"
    && replay.verified_clauses === condition.clause_count
    && replay.failed_clauses === 0
    && replay.incomplete_clauses === 0,
  `${condition.id}: clause replay is not complete`);
  assert(replay.nogoods === false && replay.conflict_backjumping === false,
    `${condition.id}: clause replay used optional search accelerators`);
  if (candidate) {
    const nextRing = new Set(polycubeCoronaRingCellKeys(candidate.voxels, manifest.model.continuation_radius));
    assert(cells.cells.every(cell => nextRing.has(String(cell))),
      `${condition.id}: cell report contains a non-next-ring cell`);
  }
}

assert(manifest.count_cover.prefix.maximum + 1 === exactCounts[0], "gap after bounded prefix");
assert(exactCounts.at(-1) + 1 === manifest.count_cover.tail.minimum, "gap before open-ended tail");
assert(manifest.conclusion?.unrestricted_radius_3_space_exhausted === true,
  "manifest does not claim unrestricted radius-three exhaustion");
assert(manifest.conclusion?.certified_non_tiler === true,
  "manifest does not record the non-tiler conclusion");
assert(manifest.conclusion?.certified_aperiodic === false,
  "a non-tiler must not be classified as aperiodic");

const summary = {
  kind: "polycube_non_tiler_count_chain_verification",
  candidate: manifest.candidate,
  classification: failures.length ? "failed" : "certified_non_tiler",
  bounded_prefix_maximum: manifest.count_cover.prefix.maximum,
  exact_counts_verified: exactCounts.length,
  exact_count_minimum: exactCounts[0] ?? null,
  exact_count_maximum: exactCounts.at(-1) ?? null,
  open_ended_tail_minimum: manifest.count_cover.tail.minimum,
  learned_clauses_replayed: manifest.sound_necessary_conditions.reduce(
    (sum, condition) => sum + condition.clause_count, 0
  ),
  next_ring_cells_checked: manifest.sound_necessary_conditions.reduce(
    (sum, condition) => sum + condition.cell_count, 0
  ),
  failures
};
process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
if (failures.length) process.exitCode = 1;
