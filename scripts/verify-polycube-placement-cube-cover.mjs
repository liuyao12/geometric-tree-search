#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const arguments_ = process.argv.slice(2);
const outputArgument = arguments_.find(argument => argument.startsWith("--output="));
const reportArguments = arguments_.filter(argument => !argument.startsWith("--"));
if (!outputArgument || !reportArguments.length) {
  throw new Error("usage: verify-polycube-placement-cube-cover.mjs --output=REPORT.json BRANCH.json ...");
}

const outputPath = resolve(outputArgument.slice("--output=".length));
const reports = reportArguments.map(path => ({
  path,
  report: JSON.parse(readFileSync(resolve(path), "utf8"))
}));
const reference = reports[0].report;
const sharedFields = [
  "key",
  "layer",
  "backend",
  "pb_solver",
  "min_placements",
  "max_placements",
  "placement_cube_cell",
  "placement_cube_candidates",
  "placement_cube_base_formula_sha256",
  "target_cells",
  "placements_considered",
  "variables",
  "constraints",
  "forbidden_clauses",
  "cell_coverability_constraints",
  "lookahead_conflict_encoding"
];

if (!reference.placement_cube_base_formula_sha256) {
  throw new Error("branch reports must include placement_cube_base_formula_sha256");
}
for (const { path, report } of reports) {
  if (report.z3_status !== "unsat" || report.classification !== "placement_cube_exhausted") {
    throw new Error(`${path} is not an exhausted placement-cube branch`);
  }
  for (const field of sharedFields) {
    if (report[field] !== reference[field]) {
      throw new Error(`${path} disagrees on shared field ${field}`);
    }
  }
}

const candidateCount = reference.placement_cube_candidates;
const owner = Array(candidateCount).fill(null);
const leaves = [];
for (const { path, report } of reports) {
  const parts = report.placement_cube_parts;
  const index = report.placement_cube_index;
  if (!Number.isInteger(parts) || parts < 2 || !Number.isInteger(index) || index < 0 || index >= parts) {
    throw new Error(`${path} has invalid placement-cube coordinates`);
  }
  const covered = [];
  for (let ordinal = index; ordinal < candidateCount; ordinal += parts) {
    if (owner[ordinal] !== null) {
      throw new Error(`${path} overlaps ${owner[ordinal]} at placement ordinal ${ordinal}`);
    }
    owner[ordinal] = path;
    covered.push(ordinal);
  }
  if (covered.length !== report.placement_cube_selected_candidates) {
    throw new Error(`${path} reports the wrong selected-candidate count`);
  }
  leaves.push({
    report: path,
    parts,
    index,
    covered_candidate_ordinals: covered,
    random_seed: report.random_seed,
    formula_cache_hit: report.formula_cache_hit,
    construction_milliseconds: report.construction_milliseconds,
    check_milliseconds: report.check_milliseconds
  });
}

const uncovered = owner.flatMap((path, ordinal) => path === null ? [ordinal] : []);
if (uncovered.length) {
  throw new Error(`placement-cube leaves leave ${uncovered.length} candidate ordinals uncovered`);
}

const certificate = {
  kind: "polycube_placement_cube_cover_certificate",
  classification: "placement_cube_cover_exhausted",
  candidate_key: reference.key,
  layer: reference.layer,
  min_placements: reference.min_placements,
  max_placements: reference.max_placements,
  anchor_cell: reference.placement_cube_cell,
  anchor_placement_candidates: candidateCount,
  covered_anchor_placement_candidates: owner.length,
  branch_leaves: leaves.length,
  placement_cube_base_formula_sha256: reference.placement_cube_base_formula_sha256,
  shared_formula: Object.fromEntries(sharedFields
    .filter(field => !field.startsWith("placement_cube_"))
    .map(field => [field, reference[field]])),
  leaves,
  warning: reference.min_placements !== null || reference.max_placements !== null
    ? "This exhausts only the stated placement-count range; it is not a non-tiling or aperiodicity certificate."
    : null
};
writeFileSync(outputPath, `${JSON.stringify(certificate, null, 2)}\n`);
process.stdout.write(`${JSON.stringify({
  type: "placement_cube_cover_certificate",
  output: outputPath,
  classification: certificate.classification,
  covered: owner.length,
  leaves: leaves.length
})}\n`);
