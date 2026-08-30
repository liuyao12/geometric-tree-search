import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readNdjson = async path => (await readFile(new URL(path, root), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const readGzipNdjson = async path => gunzipSync(await readFile(new URL(path, root)))
  .toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);

// The exact quotient backend and Prototile3D enumerate the same six proper
// A2 orientations in different orders. These affine shifts convert the
// proof's normalized alcove coordinates into the web engine's normalized
// oriented-tile coordinates, then re-root the first placement at the origin.
const proofToWebOrientation = [0, 3, 4, 1, 2, 5];
const proofOrientationTransforms = [
  [1, [0, 1, 2]], [1, [1, 2, 0]], [1, [2, 0, 1]],
  [-1, [0, 2, 1]], [-1, [1, 0, 2]], [-1, [2, 1, 0]]
];
const webPeriodicTemplate = (certificate, geometry) => {
  if (!certificate) return null;
  const proofOrientationShifts = proofOrientationTransforms.map(([sign, permutation]) =>
    [0, 1, 2].map(axis => Math.min(...geometry.v.map(vertex =>
      sign * vertex[permutation[axis]]
    )))
  );
  const rootShift = proofOrientationShifts[certificate.placements[0].orientation_index]
    .map(value => -value);
  return {
    period_vectors: certificate.period_vectors,
    motif: certificate.placements.map(placement => ({
      prototile_idx: 0,
      orientation_index: proofToWebOrientation[placement.orientation_index],
      translation: placement.translation.map((value, axis) =>
        value + proofOrientationShifts[placement.orientation_index][axis] + rootShift[axis]
      )
    }))
  };
};

const representatives = await readNdjson(
  "data/a2-sliced-alcove-size8-directed-exact6-reflection-representatives.ndjson"
);
const exactThreeById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-periodic-exact3.ndjson.gz"
)).map(record => [record.id, record]));
const exactTwelvePositiveById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-periodic-exact12-positive.ndjson.gz"
)).map(record => [record.id, record]));
const fourCopyProperById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-four-cluster-scale2-proper.ndjson.gz"
)).map(record => [record.id, record]));
const anisotropicRows = await readGzipNdjson(
  "data/a2-sliced-alcove-size8-anisotropic-cellularity-through8.ndjson.gz"
);
const fourCopyReflectedById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-four-cluster-scale2-reflected-summary.ndjson.gz"
)).map(record => [record.id, record]));
const anisotropicById = new Map();
for (const record of anisotropicRows) {
  if (!anisotropicById.has(record.id)) anisotropicById.set(record.id, []);
  anisotropicById.get(record.id).push(record);
}
const coronaById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size8-directed-corona1.ndjson"
)).map(record => [record.id, record]));
const extensionById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size8-directed-retained-corona-extension.ndjson"
)).map(record => [record.id, record]));
const corona2ById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-corona2-gcts.ndjson.gz"
)).map(record => [record.id, record]));
const radius3ById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size8-directed-radius3-gcts.ndjson.gz"
)).map(record => [record.id, record]));

if (representatives.length !== 15) {
  throw new Error(`Expected 15 reflection classes, found ${representatives.length}`);
}
if (exactTwelvePositiveById.size !== 6 || fourCopyProperById.size !== 13) {
  throw new Error("Expected six 12-copy positives and 13 four-copy substitution screens");
}
const unresolvedIds = representatives
  .map(record => record.id)
  .filter(id => !exactTwelvePositiveById.has(id));
const survivorPriorityById = new Map(unresolvedIds.map((id, index) => [id, index + 1]));

const candidates = representatives.map(record => {
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  const exactThree = exactThreeById.get(record.id);
  const exactTwelve = exactTwelvePositiveById.get(record.id);
  const fourCopyProper = fourCopyProperById.get(record.id);
  const anisotropic = anisotropicById.get(record.id) ?? [];
  const fourCopyReflected = fourCopyReflectedById.get(record.id);
  const corona = coronaById.get(record.id);
  const extension = extensionById.get(record.id);
  const corona2 = corona2ById.get(record.id);
  const radius3 = radius3ById.get(record.id);
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
  if (exactTwelve && (!exactTwelve.periodic_z3?.replay?.verified
      || exactTwelve.periodic_z3.certificate?.copies !== 12)) {
    throw new Error(`Unverified 12-copy periodic witness for ${record.id}`);
  }
  if (!exactTwelve && (!fourCopyProper?.four_copy_alcove_metatile_screen?.certified
      || fourCopyProper.classification !== "no_four_copy_metatile_scalar2_substitution")) {
    throw new Error(`Missing four-copy substitution exclusion for ${record.id}`);
  }
  if (!exactTwelve && (anisotropic.length !== 10 || anisotropic.some(item =>
    item.anisotropic_substitution_classification !== "inflation_not_alcove_cellular"
    || !item.anisotropic_substitution?.certified
    || !item.anisotropic_substitution?.noncellular_substitution_open))) {
    throw new Error(`Missing anisotropic cellularity certificate for ${record.id}`);
  }
  if (!exactTwelve && (!fourCopyReflected || (
      fourCopyReflected.classification !== "no_four_copy_metatile_scalar2_substitution"
      || !fourCopyReflected.four_copy_alcove_metatile_screen?.certified))) {
    throw new Error(`Invalid reflected four-copy exclusion for ${record.id}`);
  }
  return {
    id: record.id,
    kind: "a2_sliced_alcove_census",
    registry_id: `a2_sliced_${record.id.slice("a2sa_".length)}`,
    name: `A2 Consecutive-Layer Size-8 Candidate ${record.id.slice("a2sa_8_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: survivorPriorityById.get(record.id) ?? null,
    survivor_count: unresolvedIds.length,
    description: "Eight-alcove non-polycube lattice function coupling consecutive triangular sections x+y+z=k.",
    screening: {
      status: exactTwelve ? "periodic" : "inconclusive",
      certificate: exactTwelve ? "translational" : null,
      census_stage: exactTwelve
        ? "a2_sliced_size8_consecutive_layers_12_copy_positive_2026_08_29"
        : "a2_sliced_size8_consecutive_layers_exact_through6_12_copy_bounded_2026_08_29",
      source_pool_size: 4406,
      three_copy_periodic_certificates: 3335,
      three_copy_periodic_survivors: 1071,
      six_copy_additional_periodic_certificates: 1045,
      periodic_survivors_through_six: 26,
      periodic_survivor_reflection_classes: 15,
      periodic_twelve_copy_certificates: exactTwelvePositiveById.size,
      // Retained aliases for older saved UI state.
      six_copy_periodic_certificates: 4380,
      six_copy_periodic_survivors: 26,
      six_copy_periodic_survivor_reflection_classes: 15,
      reflection_class_size: record.reflection_class.size,
      reflection_class_members: record.reflection_class.members,
      periodic_exact_through: exactTwelve ? 12 : 6,
      periodic_requested_through: 12,
      periodic_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_three_copy_complete: exactThree.periodic_z3.hnf_range_exhausted === true,
      periodic_three_copy_exact_multicover_nodes: exactThree.periodic_z3.exact_multicover_nodes,
      periodic_six_copy_complete: record.periodic_z3.hnf_range_exhausted === true,
      periodic_six_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_three_copy_report: "data/a2-sliced-alcove-size8-directed-periodic-exact3.ndjson.gz",
      periodic_report: "data/a2-sliced-alcove-size8-directed-periodic-exact6.ndjson.gz",
      periodic_twelve_copy_certificate: exactTwelve?.periodic_z3.certificate ?? null,
      periodic_twelve_copy_replay_verified: exactTwelve?.periodic_z3.replay?.verified ?? false,
      periodic_twelve_copy_positive_report:
        "data/a2-sliced-alcove-size8-directed-periodic-exact12-positive.ndjson.gz",
      motif_tiles: exactTwelve?.periodic_z3.certificate?.copies ?? null,
      period_vectors: exactTwelve?.periodic_z3.certificate?.period_vectors ?? null,
      quotient_determinant: exactTwelve?.periodic_z3.certificate?.determinant ?? null,
      periodic_template: webPeriodicTemplate(exactTwelve?.periodic_z3.certificate, geometry),
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
      radius_three_status: radius3?.radius3_gcts_classification ?? null,
      radius_three_outer_rounds: radius3?.radius3_gcts?.outer_rounds ?? 0,
      radius_three_first_corona_failure_clauses:
        radius3?.radius3_gcts?.first_corona_failure_clauses?.length ?? 0,
      radius_three_stopped_by: radius3?.radius3_gcts?.stopped_by ?? null,
      radius_three_cumulative_milliseconds:
        radius3?.radius3_gcts?.cumulative_milliseconds ?? 0,
      radius_three_report: radius3
        ? "data/a2-sliced-alcove-size8-directed-radius3-gcts.ndjson.gz"
        : null,
      substitution_direct_scalar_scales_excluded: [2, 3, 4, 5, 6, 7, 8],
      substitution_two_copy_metatile_scalar_scales_excluded: [2, 3],
      substitution_three_copy_metatile_scalar_scales_excluded: [2, 3],
      substitution_models_exhausted: ["proper", "reflected"],
      substitution_four_copy_metatile_proper_scalar_scales_excluded:
        fourCopyProper ? [2] : [],
      substitution_four_copy_metatile_types_exhausted:
        fourCopyProper?.four_copy_alcove_metatile_screen?.symmetry_distinct_metatiles ?? null,
      substitution_four_copy_report:
        "data/a2-sliced-alcove-size8-four-cluster-scale2-proper.ndjson.gz",
      substitution_four_copy_reflected_scalar_scales_excluded:
        fourCopyReflected ? [2] : [],
      substitution_four_copy_reflected_types_exhausted:
        fourCopyReflected?.four_copy_alcove_metatile_screen
          ?.symmetry_distinct_metatiles ?? null,
      substitution_four_copy_reflected_report: fourCopyReflected
        ? "data/a2-sliced-alcove-size8-four-cluster-scale2-reflected.ndjson.gz"
        : null,
      substitution_anisotropic_cellular_inflations_excluded: anisotropic.length,
      substitution_anisotropic_cellular_scale_pairs: anisotropic.map(item => [
        item.anisotropic_substitution.planar_scale,
        item.anisotropic_substitution.layer_scale
      ]),
      substitution_anisotropic_claim_scope:
        "fixed_affine_A3_alcove_cellular_substitution_only",
      substitution_noncellular_inflations_open: true,
      substitution_anisotropic_report:
        "data/a2-sliced-alcove-size8-anisotropic-cellularity-through8.ndjson.gz"
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
