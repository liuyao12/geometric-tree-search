import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readNdjson = async path => (await readFile(new URL(path, root), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const readGzipNdjson = async path => gunzipSync(await readFile(new URL(path, root)))
  .toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);

const representatives = await readNdjson(
  "data/a2-sliced-alcove-size8-directed-exact6-reflection-representatives.ndjson"
);
const exactThreeById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-periodic-exact3.ndjson.gz"
)).map(record => [record.id, record]));
const coronaById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size8-directed-corona1.ndjson"
)).map(record => [record.id, record]));
const extensionById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size8-directed-retained-corona-extension.ndjson"
)).map(record => [record.id, record]));
const corona2ById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-corona2-gcts.ndjson.gz"
)).map(record => [record.id, record]));

if (representatives.length !== 15) {
  throw new Error(`Expected 15 reflection classes, found ${representatives.length}`);
}

const candidates = representatives.map(record => {
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  const exactThree = exactThreeById.get(record.id);
  const corona = coronaById.get(record.id);
  const extension = extensionById.get(record.id);
  const corona2 = corona2ById.get(record.id);
  if (exactThree?.classification !== "unresolved"
      || !exactThree.periodic_z3?.hnf_range_exhausted
      || !corona?.corona_z3?.replay?.verified || !extension) {
    throw new Error(`Missing replayed corona evidence for ${record.id}`);
  }
  const directRadius2 = extension.retained_corona_extension_classification === "radius2_witness";
  const cegarRadius2 = corona2?.corona2_core_classification === "radius2_witness";
  const radius2Evidence = directRadius2
    ? extension.retained_corona_extension
    : cegarRadius2 ? corona2.corona2_core_cegar : null;
  if (radius2Evidence && !radius2Evidence.replay?.verified) {
    throw new Error(`Unverified radius-two witness for ${record.id}`);
  }
  return {
    id: record.id,
    kind: "a2_sliced_alcove_census",
    registry_id: `a2_sliced_${record.id.slice("a2sa_".length)}`,
    name: `A2 Consecutive-Layer Size-8 Candidate ${record.id.slice("a2sa_8_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: record.survivor_priority,
    survivor_count: representatives.length,
    description: "Eight-alcove non-polycube lattice function coupling consecutive triangular sections x+y+z=k.",
    screening: {
      status: "inconclusive",
      certificate: null,
      census_stage: "a2_sliced_size8_consecutive_layers_exact_through6_2026_08_29",
      source_pool_size: 4406,
      three_copy_periodic_certificates: 3335,
      three_copy_periodic_survivors: 1071,
      six_copy_additional_periodic_certificates: 1045,
      periodic_survivors_through_six: 26,
      periodic_survivor_reflection_classes: 15,
      // Retained aliases for older saved UI state.
      six_copy_periodic_certificates: 4380,
      six_copy_periodic_survivors: 26,
      six_copy_periodic_survivor_reflection_classes: 15,
      reflection_class_size: record.reflection_class.size,
      reflection_class_members: record.reflection_class.members,
      periodic_exact_through: 6,
      periodic_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_three_copy_complete: exactThree.periodic_z3.hnf_range_exhausted === true,
      periodic_three_copy_exact_multicover_nodes: exactThree.periodic_z3.exact_multicover_nodes,
      periodic_six_copy_complete: record.periodic_z3.hnf_range_exhausted === true,
      periodic_six_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_three_copy_report: "data/a2-sliced-alcove-size8-directed-periodic-exact3.ndjson.gz",
      periodic_report: "data/a2-sliced-alcove-size8-directed-periodic-exact6.ndjson.gz",
      corona_completed_radius: 1,
      corona_completed_verified: true,
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_placements_considered: corona.corona_z3.placements_considered,
      corona_report: "data/a2-sliced-alcove-size8-directed-corona1.ndjson",
      retained_corona_extension_status: extension.retained_corona_extension_classification,
      retained_corona_extension_report:
        "data/a2-sliced-alcove-size8-directed-retained-corona-extension.ndjson",
      radius_two_status: radius2Evidence ? "radius2_witness" : "unresolved",
      radius_two_patch_copies: radius2Evidence?.replay?.patch_copies ?? null,
      radius_two_completed_verified: radius2Evidence?.replay?.verified ?? false,
      radius_two_failure_clauses: corona2?.corona2_core_cegar?.clauses?.length ?? 0,
      radius_two_stopped_by: corona2?.corona2_core_cegar?.stopped_by ?? null,
      radius_two_report: corona2
        ? "data/a2-sliced-alcove-size8-directed-corona2-gcts.ndjson.gz"
        : "data/a2-sliced-alcove-size8-directed-retained-corona-extension.ndjson",
      substitution_direct_scalar_scales_excluded: [2, 3, 4, 5, 6, 7, 8],
      substitution_two_copy_metatile_scalar_scales_excluded: [2, 3],
      substitution_three_copy_metatile_scalar_scales_excluded: [2, 3],
      substitution_models_exhausted: ["proper", "reflected"]
    },
    shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
  };
});

const source = `// Generated by scripts/build-a2-sliced-size8-catalog.mjs.\n`
  + `export const A2_SLICED_SIZE8_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-sliced-size8-candidates.js", root), source, "utf8");
console.log(JSON.stringify({
  candidates: candidates.length,
  radius_two_witnesses: candidates.filter(candidate =>
    candidate.screening.radius_two_status === "radius2_witness").length,
  ids: candidates.map(candidate => candidate.id)
}, null, 2));
