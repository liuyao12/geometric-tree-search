#!/usr/bin/env node
/** Build the leading candidates recovered from the complete size-nine census. */

import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readGzipNdjson = async relativePath => gunzipSync(
  await readFile(new URL(relativePath, root))
).toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);

const exactEight = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-focused-periodic-exact8-bounded.ndjson.gz"
);
const exactSix = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-exact6-reflection-representatives.ndjson.gz"
);
const exactCorona = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-focused-corona1-bounded.ndjson.gz"
);
const directSubstitutions = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-direct-substitution-scale2to8.ndjson.gz"
);
const coronaOverrides = [
  ...(await readGzipNdjson("data/a2-sliced-size9-palindromic-corona-z3-04636.ndjson.gz")),
  ...(await readGzipNdjson("data/a2-sliced-size9-palindromic-corona-z3-04468.ndjson.gz"))
];
const coronaById = new Map(exactCorona.map(record => [record.id, record]));
for (const record of coronaOverrides) coronaById.set(record.id, record);

const selectedIds = ["a2sp_9_04636", "a2sp_9_01085", "a2sp_9_04468"];
const periodicById = new Map(exactEight.map(record => [record.id, record]));
const exactSixById = new Map(exactSix.map(record => [record.id, record]));
const directSubstitutionById = Map.groupBy
  ? Map.groupBy(directSubstitutions, record => record.id)
  : directSubstitutions.reduce((groups, record) => {
      const rows = groups.get(record.id) ?? [];
      rows.push(record);
      groups.set(record.id, rows);
      return groups;
    }, new Map());
const candidates = selectedIds.map((id, index) => {
  const record = periodicById.get(id);
  const sixCopy = exactSixById.get(id);
  const corona = coronaById.get(id);
  const direct = directSubstitutionById.get(id) ?? [];
  if (!record || !sixCopy || !corona) throw new Error(`Missing focused receipt for ${id}`);
  if (record.classification !== "unresolved"
      || record.periodic_z3.stopped_by !== "candidate_time_limit") {
    throw new Error(`Expected bounded eight-copy result for ${id}`);
  }
  if (corona.corona_classification !== "root_corona_exists"
      || corona.corona_z3.replay?.verified !== true) {
    throw new Error(`Missing replayed root corona for ${id}`);
  }
  if (direct.length !== 14 || direct.some(result =>
    result.alcove_substitution_classification !== "no_direct_scalar_substitution"
    || result.alcove_substitution.certified !== true
    || result.alcove_substitution.independent_replay?.verified !== true)) {
    throw new Error(`Missing replayed scale-2-through-8 substitution exclusions for ${id}`);
  }
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  return {
    id,
    kind: "a2_sliced_palindromic_alcove_census",
    registry_id: `a2_sliced_pal_${id.slice("a2sp_".length)}`,
    name: `A2 Palindromic-Profile Size-9 Candidate ${id.slice("a2sp_9_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: index + 1,
    survivor_count: 97,
    description: "Nine-alcove non-polycube from the completed palindromic-profile stratum on consecutive x+y+z=k sections.",
    screening: {
      status: "inconclusive",
      certificate: null,
      census_stage: "a2_sliced_size9_complete_palindromic_profile_2026_08_30",
      complete_source_pool_size: 22607,
      recovered_source_pool_size: 1627,
      recovered_two_copy_periodic_certificates: 1135,
      recovered_four_copy_additional_periodic_certificates: 304,
      recovered_reflection_classes_through_four: 114,
      recovered_six_copy_additional_periodic_classes: 17,
      recovered_reflection_classes_through_six: 97,
      periodic_exact_through: 6,
      periodic_six_copy_hnf_total: sixCopy.periodic_z3.hnf_total,
      periodic_six_copy_hnf_covered: sixCopy.periodic_z3.hnf_covered,
      periodic_six_copy_solver_unknowns: 0,
      periodic_six_copy_exact_multicover_nodes: sixCopy.periodic_z3.exact_multicover_nodes,
      periodic_eight_copy_bounded_hnf_visited: record.periodic_z3.hnf_visited,
      periodic_eight_copy_bounded_hnf_covered: record.periodic_z3.hnf_covered,
      periodic_eight_copy_hnf_total: record.periodic_z3.hnf_total,
      periodic_eight_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_eight_copy_stopped_by: record.periodic_z3.stopped_by,
      periodic_eight_copy_candidate_time_limit_ms: 60000,
      periodic_eight_copy_exact_node_limit: 500000,
      direct_scalar_substitution_exact_scales: [2, 8],
      direct_scalar_substitution_models: ["proper", "reflected"],
      direct_scalar_substitution_certified_negatives: direct.length,
      direct_scalar_substitution_report: "data/a2-sliced-size9-palindromic-direct-substitution-scale2to8.ndjson.gz",
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_solver: corona.corona_z3.smt2_sha256 ? "z3" : "exact_gcts",
      corona_report: corona.corona_z3.smt2_sha256
        ? `data/a2-sliced-size9-palindromic-corona-z3-${id.slice("a2sp_9_".length)}.ndjson.gz`
        : "data/a2-sliced-size9-palindromic-focused-corona1-bounded.ndjson.gz",
      periodic_report: "data/a2-sliced-size9-palindromic-focused-periodic-exact8-bounded.ndjson.gz"
    },
    root_corona_witness: corona.corona_z3.witness
  };
});

await writeFile(
  new URL("assets/a2-sliced-size9-palindromic-candidates.js", root),
  `// Generated by scripts/build-a2-sliced-size9-palindromic-catalog.mjs.\n`
    + `export const A2_SLICED_SIZE9_PALINDROMIC_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`,
  "utf8"
);
console.log(JSON.stringify({ candidates: selectedIds }, null, 2));
