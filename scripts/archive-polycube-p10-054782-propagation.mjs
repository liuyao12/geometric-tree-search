#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { verifyPolycubeCoronaPatch } from "../assets/polycube-corona-search.js";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const runDirectory = resolve(root, "runs/p10-054782-exact41-propagate-values-benchmark-v1");
const output = resolve(
  process.argv.find(argument => argument.startsWith("--output="))?.slice("--output=".length)
    ?? resolve(root, "data/polycube-p10-054782-propagate-values-nested-screen-2026-08-24.json")
);
const load = path => JSON.parse(readFileSync(resolve(path), "utf8"));
const digest = path => createHash("sha256").update(readFileSync(resolve(path))).digest("hex");
const run = name => resolve(runDirectory, name);
const summarizeSolver = report => ({
  placement_cube_parts: report.placement_cube_parts,
  placement_cube_index: report.placement_cube_index,
  placement_cube_candidates: report.placement_cube_candidates,
  selected_candidates: report.placement_cube_selected_candidates,
  required_placements: report.required_placements ?? 0,
  z3_status: report.z3_status,
  classification: report.classification,
  construction_milliseconds: report.construction_milliseconds,
  check_milliseconds: report.check_milliseconds,
  random_seed: report.random_seed,
  base_formula_sha256: report.placement_cube_base_formula_sha256
});
const checkedLeaf = (name, expectedStatus = "unsat") => {
  const path = run(name);
  const report = load(path);
  assert.equal(report.propagate_values, true, `${name} did not use fixed-value propagation`);
  assert.equal(report.z3_status, expectedStatus, `${name} has the wrong terminal status`);
  return { report: `runs/${runDirectory.split("/").at(-1)}/${name}`, sha256: digest(path), ...summarizeSolver(report) };
};

const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p10-054782");
assert(candidate);
const proposalPath = run("parts64-index33-solver-seed2933-300s.json");
const proposal = load(proposalPath);
assert.equal(proposal.z3_status, "sat");
assert.equal(proposal.corona.length, 41);
const proposalVerification = verifyPolycubeCoronaPatch(candidate.voxels, proposal.corona, 3);
assert.equal(proposalVerification.verified, true);

const continuationPath = run("parts64-index33-seed2933-radius4-continuation.json");
const continuation = load(continuationPath);
assert.equal(continuation.classification, "fixed_witnesses_exhausted");
assert.equal(continuation.fixed_witness_continuations.length, 1);
assert.equal(continuation.fixed_witness_continuations[0].exhausted, true);
assert.equal(continuation.fixed_witness_continuations[0].nodes, 2);

const newNogoodPath = run("parts64-index33-seed2933-radius4-nogoods.json");
const newNogoods = load(newNogoodPath);
const newReplayPath = run("parts64-index33-seed2933-radius4-nogood-replay.json");
const newReplay = load(newReplayPath);
assert.equal(newNogoods.clauses.length, 13);
assert.equal(newReplay.classification, "verified");
assert.equal(newReplay.verified_clauses, 13);
assert.equal(newReplay.failed_clauses, 0);

const combinedPath = run("feedback-58-clauses.json");
const combined = load(combinedPath);
const combinedReplayPath = run("feedback-58-clause-replay.json");
const combinedReplay = load(combinedReplayPath);
assert.equal(combined.clauses.length, 58);
assert.equal(combinedReplay.classification, "verified");
assert.equal(combinedReplay.verified_clauses, 58);
assert.equal(combinedReplay.failed_clauses, 0);

const historicalLeaves = [
  checkedLeaf("parts64-index16-seed2816-240s.json"),
  checkedLeaf("parts64-index32-seed2632.json"),
  { report: `runs/${runDirectory.split("/").at(-1)}/parts64-index33-solver-seed2933-300s.json`, sha256: digest(proposalPath), ...summarizeSolver(proposal) },
  checkedLeaf("parts64-index48-seed2648.json"),
  checkedLeaf("parts64-index49-seed2649.json"),
  checkedLeaf("parts128-index65-seed2600.json")
];

const levelTwoClosed = [0, 1, 2, 4, 5, 7].map(index =>
  checkedLeaf(`nested-parts8-index${index}-seed${3300 + index}.json`)
);
const branchThreeThirdClosed = checkedLeaf("nested-branch3-third-index1-seed3501.json");
const branchThreeFourthClosed = Array.from({ length: 9 }, (_, index) =>
  checkedLeaf(`fourth-3f-index${index}-seed${3700 + index}.json`)
);
const branchSixThirdClosed = checkedLeaf("nested-branch6-third-index1-seed3561.json");
const branchSixFourthClosed = checkedLeaf("fourth-6f-index1-seed3601.json");
const openLeafPath = run("fourth-6f-index0-seed3600.json");
const openLeaf = load(openLeafPath);
assert.equal(openLeaf.z3_status, "unknown");
assert.equal(openLeaf.reason_unknown, "timeout");
const openRequiredPath = run("index33-nested6-fourth0-required-placements.json");
const openRequired = load(openRequiredPath);
assert.equal(openRequired.placement_keys.length, 4);

const exactAvailabilityReports = [2500, 2501].map(seed => {
  const path = resolve(root, `runs/p10-054782-exact41-exact-availability-benchmark-v1/parts128-index65-seed${seed}.json`);
  const report = load(path);
  assert.equal(report.exact_availability, true);
  assert.equal(report.z3_status, "unknown");
  return { random_seed: seed, check_milliseconds: report.check_milliseconds, z3_status: report.z3_status };
});

const archive = {
  kind: "polycube_exact41_propagation_and_nested_partition_screen",
  generated_at: "2026-08-24",
  candidate: candidate.id,
  candidate_key: proposal.key,
  model: {
    outer_radius: 3,
    continuation_radius: 4,
    exact_placements: 41,
    proper_rotations_only: true,
    root_fixed: true,
    next_ring_coverability_cells: 47
  },
  solver_improvement: {
    option: "--propagate-values",
    method: "run Z3 fixed-value propagation before pseudo-Boolean bit-blasting",
    production_default_in_placement_cube_cegar: true,
    historical_singleton_leaves: historicalLeaves,
    historical_unsat_leaves: historicalLeaves.filter(leaf => leaf.z3_status === "unsat").length,
    historical_sat_proposals: historicalLeaves.filter(leaf => leaf.z3_status === "sat").length,
    exact_availability_control: {
      promoted: false,
      reason: "Both matched 120-second trials remained unknown and the encoding added 7,754 reverse constraints.",
      trials: exactAvailabilityReports
    }
  },
  new_radius3_proposal: {
    placements: proposal.corona.length,
    source_report_sha256: digest(proposalPath),
    verification: proposalVerification,
    construction_milliseconds: proposal.construction_milliseconds,
    check_milliseconds: proposal.check_milliseconds,
    corona: proposal.corona
  },
  exact_radius4_feedback: {
    continuation_exhausted: true,
    continuation_nodes: continuation.fixed_witness_continuations[0].nodes,
    continuation_milliseconds: continuation.fixed_witness_continuations[0].milliseconds,
    immediate_obstructions: continuation.fixed_witness_continuations[0].immediate_dead_target_count,
    new_clauses: newNogoods.clauses,
    new_clause_report_sha256: digest(newNogoodPath),
    new_clause_replay: {
      classification: newReplay.classification,
      verified_clauses: newReplay.verified_clauses,
      failed_clauses: newReplay.failed_clauses,
      total_nodes: newReplay.total_nodes,
      total_milliseconds: newReplay.total_milliseconds,
      report_sha256: digest(newReplayPath)
    },
    combined_feedback_clauses: combined.clauses.length,
    combined_report_sha256: digest(combinedPath),
    combined_replay: {
      classification: combinedReplay.classification,
      verified_clauses: combinedReplay.verified_clauses,
      failed_clauses: combinedReplay.failed_clauses,
      total_nodes: combinedReplay.total_nodes,
      total_milliseconds: combinedReplay.total_milliseconds,
      report_sha256: digest(combinedReplayPath)
    }
  },
  nested_partition: {
    first_required_placement: load(run("index33-required-placement.json")).placement_keys,
    level_two: {
      split_cell: "0,1,1",
      compatible_candidates: 8,
      closed_indices: [0, 1, 2, 4, 5, 7],
      closed_leaves: levelTwoClosed,
      refined_indices: [3, 6]
    },
    refined_branch_3: {
      split_cell: "1,1,-1",
      compatible_candidates: 2,
      closed_index_1: branchThreeThirdClosed,
      refined_index_0: {
        split_cell: "0,0,-2",
        compatible_candidates: 9,
        closed_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8],
        closed_leaves: branchThreeFourthClosed
      }
    },
    refined_branch_6: {
      split_cell: "1,1,-1",
      compatible_candidates: 2,
      closed_index_1: branchSixThirdClosed,
      refined_index_0: {
        split_cell: "0,2,-1",
        compatible_candidates: 2,
        closed_index_1: branchSixFourthClosed,
        open_index_0: {
          source_report_sha256: digest(openLeafPath),
          ...summarizeSolver(openLeaf),
          required_placement_keys: openRequired.placement_keys,
          next_recommended_split_cells: [
            { cell: "-1,2,0", compatible_candidates: 9 },
            { cell: "0,0,-2", compatible_candidates: 9 }
          ]
        }
      }
    },
    exact_unsat_partition_leaves: 18,
    open_partition_leaves: 1,
    exact41_exhausted: false
  },
  interpretation: "Fixed-value PB preprocessing turns the old six-singleton timeout residue into five exact UNSAT leaves plus one new 41-copy proposal. GCTS rejects that proposal at radius four and supplies 13 independently replayed clauses. Nested compatible-placement partitioning then reduces the remaining model space to one explicit four-placement path. Exact count 41 remains open, so this is neither a non-tiling nor an aperiodicity certificate.",
  warning: "Finite-radius exhaustion under learned continuation clauses does not prove non-tiling or aperiodicity until every exact placement count and the unbounded tail are covered."
};

mkdirSync(dirname(output), { recursive: true });
writeFileSync(output, `${JSON.stringify(archive, null, 2)}\n`);
process.stdout.write(`${JSON.stringify({
  output,
  proposal_placements: archive.new_radius3_proposal.placements,
  replayed_clauses: archive.exact_radius4_feedback.combined_replay.verified_clauses,
  exact_unsat_partition_leaves: archive.nested_partition.exact_unsat_partition_leaves,
  open_partition_leaves: archive.nested_partition.open_partition_leaves
})}\n`);
