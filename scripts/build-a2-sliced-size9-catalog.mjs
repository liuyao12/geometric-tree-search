import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readNdjson = async path => {
  const contents = await readFile(new URL(path, root));
  const text = path.endsWith(".gz") ? gunzipSync(contents).toString("utf8") : contents.toString("utf8");
  return text
  .trim().split("\n").filter(Boolean).map(JSON.parse);
};

// The quotient prover and Prototile3D enumerate the same six proper A2
// orientations in different orders. Convert a replayed proof motif to the
// web engine's normalized oriented-tile coordinates.
const proofToWebOrientation = [0, 3, 4, 1, 2, 5];
const proofOrientationTransforms = [
  [1, [0, 1, 2]], [1, [1, 2, 0]], [1, [2, 0, 1]],
  [-1, [0, 2, 1]], [-1, [1, 0, 2]], [-1, [2, 1, 0]]
];
const webPeriodicTemplate = (certificate, geometry) => {
  if (!certificate) return null;
  const shifts = proofOrientationTransforms.map(([sign, permutation]) =>
    [0, 1, 2].map(axis => Math.min(...geometry.v.map(vertex =>
      sign * vertex[permutation[axis]]
    )))
  );
  const rootShift = shifts[certificate.placements[0].orientation_index].map(value => -value);
  return {
    period_vectors: certificate.period_vectors,
    motif: certificate.placements.map(placement => ({
      prototile_idx: 0,
      orientation_index: proofToWebOrientation[placement.orientation_index],
      translation: placement.translation.map((value, axis) =>
        value + shifts[placement.orientation_index][axis] + rootShift[axis]
      )
    }))
  };
};

const sourcePath = "runs/a2-sliced-size9-exact8-top8-merged.ndjson";
const records = await readNdjson(sourcePath);
if (records.length !== 8) throw new Error(`Expected eight focused records, found ${records.length}`);
const unresolved = records.filter(record => record.classification === "unresolved");
const periodic = records.filter(record => record.classification === "periodic");
const scalarFamilyRows = await readNdjson(
  "data/a2-sliced-alcove-size9-scalar-family-certificates.ndjson"
);
const scalarFamilyById = Map.groupBy(scalarFamilyRows, record => record.id);
const coronaRows = await readNdjson("runs/a2-sliced-size9-corona1.ndjson");
const coronaById = new Map(coronaRows.map(record => [record.id, record]));
const radiusTwoRows = await readNdjson("runs/a2-sliced-size9-corona2-focused256-merged.ndjson");
const radiusTwoById = new Map(radiusTwoRows.map(record => [record.id, record]));
const threeCopyRows = [];
for (const record of records.filter(item => item.classification === "unresolved")) {
  for (const scale of [2, 3]) for (const model of ["proper", "reflected"]) {
    const path = `runs/a2-sliced-size9-three-scale${scale}-${model}-${record.id.slice("a2sa_9_".length)}.ndjson`;
    const [screen] = await readNdjson(path);
    const detail = screen?.three_copy_alcove_metatile_screen;
    if (!detail?.certified
        || screen.classification !== `no_three_copy_metatile_scalar${scale}_substitution`
        || detail.include_reflections !== (model === "reflected")
        || detail.parents_completed !== detail.symmetry_distinct_metatiles) {
      throw new Error(`Incomplete three-copy substitution exclusion in ${path}`);
    }
    threeCopyRows.push({
      id: record.id,
      classification: screen.classification,
      scale,
      model,
      certified: true,
      symmetry_distinct_metatiles: detail.symmetry_distinct_metatiles,
      parents_completed: detail.parents_completed,
      canonical_sha256: detail.canonical_sha256,
      parent_counts: detail.parent_counts
    });
  }
}
const threeCopyById = Map.groupBy(threeCopyRows, record => record.id);
const fourCopyRows = [];
for (const record of unresolved) {
  const path = `runs/a2-sliced-size9-four-scale2-proper-${record.id.slice("a2sa_9_".length)}-merged.ndjson`;
  const [screen] = await readNdjson(path);
  const detail = screen?.four_copy_alcove_metatile_screen;
  if (!detail?.certified
      || screen.classification !== "no_four_copy_metatile_scalar2_substitution"
      || detail.include_reflections !== false
      || detail.parent_range?.[0] !== 0
      || detail.parent_range?.[1] !== detail.symmetry_distinct_metatiles
      || detail.parents_completed !== detail.symmetry_distinct_metatiles
      || detail.parent_counts?.unresolved !== 0) {
    throw new Error(`Incomplete four-copy substitution exclusion in ${path}`);
  }
  fourCopyRows.push({
    id: record.id,
    classification: screen.classification,
    scale: 2,
    model: "proper",
    certified: true,
    symmetry_distinct_metatiles: detail.symmetry_distinct_metatiles,
    parents_completed: detail.parents_completed,
    canonical_sha256: detail.canonical_sha256,
    parent_counts: detail.parent_counts,
    range_receipts: detail.range_receipts
  });
}
const fourCopyById = new Map(fourCopyRows.map(record => [record.id, record]));
const reflectedFourCopyRows = [];
const completedReflectedFourCopyIds = new Set(unresolved.map(record => record.id));
for (const record of unresolved.filter(item => completedReflectedFourCopyIds.has(item.id))) {
  const path = `data/a2-sliced-alcove-size9-four-cluster-scale2-reflected-${record.id.slice("a2sa_9_".length)}.ndjson.gz`;
  const [screen] = await readNdjson(path);
  const detail = screen?.four_copy_alcove_metatile_screen;
  if (!detail?.certified
      || screen.classification !== "no_four_copy_metatile_scalar2_substitution"
      || detail.include_reflections !== true
      || detail.parent_range?.[0] !== 0
      || detail.parent_range?.[1] !== detail.symmetry_distinct_metatiles
      || detail.parents_completed !== detail.symmetry_distinct_metatiles
      || detail.parent_counts?.unresolved !== 0) {
    throw new Error(`Incomplete reflected four-copy substitution exclusion in ${path}`);
  }
  reflectedFourCopyRows.push({
    id: record.id,
    classification: screen.classification,
    scale: 2,
    model: "reflected",
    certified: true,
    symmetry_distinct_metatiles: detail.symmetry_distinct_metatiles,
    parents_completed: detail.parents_completed,
    canonical_sha256: detail.canonical_sha256,
    parent_counts: detail.parent_counts,
    range_receipts: detail.range_receipts
  });
}
const reflectedFourCopyById = new Map(
  reflectedFourCopyRows.map(record => [record.id, record])
);
const twoCopyRows = [];
const twoCopyCampaigns = [];
for (const scale of [2, 3]) for (const model of ["proper", "reflected"]) {
  const path = `runs/a2-sliced-size9-two-scale${scale}-${model}.ndjson`;
  const rows = await readNdjson(path);
  if (rows.length !== 356) throw new Error(`Expected 356 rows in ${path}, found ${rows.length}`);
  for (const screen of rows) {
    const detail = screen.two_copy_alcove_metatile_screen;
    if (!detail?.certified
        || screen.classification !== `no_two_copy_metatile_scalar${scale}_substitution`
        || detail.include_reflections !== (model === "reflected")
        || detail.parents_completed !== detail.symmetry_distinct_metatiles) {
      throw new Error(`Incomplete two-copy substitution exclusion for ${screen.id} in ${path}`);
    }
    if (unresolved.some(record => record.id === screen.id)) twoCopyRows.push({
      id: screen.id,
      classification: screen.classification,
      scale,
      model,
      certified: true,
      symmetry_distinct_metatiles: detail.symmetry_distinct_metatiles,
      parents_completed: detail.parents_completed,
      canonical_sha256: detail.canonical_sha256,
      parent_counts: detail.parent_counts
    });
  }
  twoCopyCampaigns.push({
    scale,
    model,
    candidates: rows.length,
    certified_negatives: rows.length,
    record_digest_sha256: createHash("sha256").update(rows.map(screen => {
      const detail = screen.two_copy_alcove_metatile_screen;
      return `${screen.id}:${detail.canonical_sha256}:${detail.parents_completed}`;
    }).sort().join("\n")).digest("hex")
  });
}
const twoCopyById = Map.groupBy(twoCopyRows, record => record.id);
if (unresolved.length !== 3 || periodic.length !== 5) {
  throw new Error(`Expected three unresolved and five periodic records; got ${unresolved.length}/${periodic.length}`);
}
for (const record of records) {
  if (record.classification === "periodic" && !record.periodic_z3?.replay?.verified) {
    throw new Error(`Unverified periodic certificate for ${record.id}`);
  }
  if (record.classification === "unresolved" && (
    !record.periodic_z3?.hnf_range_exhausted
    || record.periodic_z3?.solver_unknown !== 0
    || record.periodic_z3?.exhausted_by_copies?.[8] !== 455
  )) throw new Error(`Incomplete exact-eight exclusion for ${record.id}`);
}

const priority = new Map(unresolved.map((record, index) => [record.id, index + 1]));
const candidates = records.map(record => {
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  const certificate = record.periodic_z3.certificate ?? null;
  const isPeriodic = record.classification === "periodic";
  const corona = coronaById.get(record.id);
  const radiusTwo = radiusTwoById.get(record.id)?.corona2_core_cegar;
  const threeCopy = threeCopyById.get(record.id) ?? [];
  const twoCopy = twoCopyById.get(record.id) ?? [];
  const fourCopy = fourCopyById.get(record.id);
  const reflectedFourCopy = reflectedFourCopyById.get(record.id);
  const scalarFamily = scalarFamilyById.get(record.id) ?? [];
  const scalarFamilyComplete = scalarFamily.length === 2
    && new Set(scalarFamily.map(item =>
      item.scalar_family_atomic_obstruction?.include_reflections
    )).size === 2
    && scalarFamily.every(item =>
      item.classification === "no_direct_scalar_substitution_all_integer_scales"
      && item.scalar_family_atomic_obstruction?.certified === true
      && item.scalar_family_atomic_obstruction?.integer_scale_range?.[0] === 2
      && item.scalar_family_atomic_obstruction?.integer_scale_range?.[1] === null
    );
  if (!corona?.corona_z3?.replay?.verified) {
    throw new Error(`Missing replayed root corona for ${record.id}`);
  }
  return {
    id: record.id,
    kind: "a2_sliced_alcove_census",
    registry_id: `a2_sliced_${record.id.slice("a2sa_".length)}`,
    name: `A2 Consecutive-Layer Size-9 ${isPeriodic ? "Periodic Control" : "Candidate"} ${record.id.slice("a2sa_9_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: priority.get(record.id) ?? null,
    survivor_count: unresolved.length,
    description: "Nine-alcove non-polycube lattice function coupling consecutive triangular sections x+y+z=k.",
    screening: {
      status: isPeriodic ? "periodic" : "inconclusive",
      certificate: isPeriodic ? "translational" : null,
      census_stage: isPeriodic
        ? "a2_sliced_size9_consecutive_layers_8_copy_positive_2026_08_30"
        : "a2_sliced_size9_consecutive_layers_exact_through8_2026_08_30",
      source_pool_size: 20980,
      two_copy_periodic_certificates: 17731,
      two_copy_periodic_survivors: 3249,
      four_copy_additional_periodic_certificates: 2300,
      periodic_survivors_through_four: 949,
      periodic_survivor_reflection_classes_through_four: 565,
      six_copy_additional_periodic_certificates: 209,
      periodic_survivor_reflection_classes_through_six: 356,
      focused_eight_copy_candidates: records.length,
      focused_eight_copy_periodic_certificates: periodic.length,
      focused_eight_copy_survivors: unresolved.length,
      reflection_class_size: record.reflection_class.size,
      reflection_class_members: record.reflection_class.members,
      periodic_exact_through: isPeriodic ? 8 : 8,
      periodic_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_eight_copy_complete: record.periodic_z3.hnf_range_exhausted === true,
      periodic_eight_copy_hnf_total: record.periodic_z3.hnf_total,
      periodic_eight_copy_orbit_representatives: record.periodic_z3.hnf_orbit_total,
      periodic_eight_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_eight_copy_exact_multicover_triples: record.periodic_z3.exact_multicover_mitm_triples,
      periodic_eight_copy_exact_multicover_quadruples: record.periodic_z3.exact_multicover_mitm_quadruples,
      periodic_eight_copy_certificate: certificate,
      periodic_eight_copy_replay_verified: record.periodic_z3.replay?.verified ?? false,
      motif_tiles: certificate?.copies ?? null,
      period_vectors: certificate?.period_vectors ?? null,
      quotient_determinant: certificate?.determinant ?? null,
      periodic_template: webPeriodicTemplate(certificate, geometry),
      periodic_report: "data/a2-sliced-alcove-size9-focused-periodic-exact8.ndjson",
      corona_completed_radius: 1,
      corona_completed_verified: true,
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_placements_considered: corona.corona_z3.placements_considered,
      corona_search_nodes: corona.corona_z3.exact_gcts?.nodes ?? null,
      corona_report: "data/a2-sliced-alcove-size9-focused-corona1.ndjson",
      substitution_direct_scalar_scales_excluded: [2, 3, 4, 5, 6, 7, 8],
      substitution_direct_scalar_integer_scales_excluded_from:
        scalarFamilyComplete ? 2 : null,
      substitution_direct_scalar_all_scale_models_exhausted:
        scalarFamilyComplete ? ["proper", "reflected"] : [],
      substitution_direct_scalar_all_scale_report: scalarFamilyComplete
        ? "data/a2-sliced-alcove-size9-scalar-family-certificates.ndjson"
        : null,
      substitution_models_exhausted: ["proper", "reflected"],
      substitution_two_copy_metatile_scalar_scales_excluded:
        twoCopy.length === 4 ? [2, 3] : [],
      substitution_two_copy_models_exhausted:
        twoCopy.length === 4 ? ["proper", "reflected"] : [],
      substitution_two_copy_types_exhausted: Object.fromEntries(twoCopy.map(item => [
        `${item.model}_scale${item.scale}`, item.symmetry_distinct_metatiles
      ])),
      substitution_two_copy_census_candidates_exhausted: 356,
      substitution_two_copy_report:
        "data/a2-sliced-alcove-size9-two-copy-census-summary.json",
      substitution_three_copy_metatile_scalar_scales_excluded:
        threeCopy.length === 4 ? [2, 3] : [],
      substitution_three_copy_models_exhausted:
        threeCopy.length === 4 ? ["proper", "reflected"] : [],
      substitution_three_copy_types_exhausted: Object.fromEntries(threeCopy.map(item => [
        `${item.model}_scale${item.scale}`, item.symmetry_distinct_metatiles
      ])),
      substitution_three_copy_report: threeCopy.length
        ? "data/a2-sliced-alcove-size9-focused-three-copy-summary.ndjson"
        : null,
      substitution_four_copy_metatile_proper_scalar_scales_excluded:
        fourCopy ? [2] : [],
      substitution_four_copy_metatile_types_exhausted:
        fourCopy?.symmetry_distinct_metatiles ?? null,
      substitution_four_copy_report: fourCopy
        ? "data/a2-sliced-alcove-size9-focused-four-copy-proper-summary.ndjson"
        : null,
      substitution_four_copy_reflected_scalar_scales_excluded:
        reflectedFourCopy ? [2] : [],
      substitution_four_copy_reflected_types_exhausted:
        reflectedFourCopy?.symmetry_distinct_metatiles ?? null,
      substitution_four_copy_reflected_report: reflectedFourCopy
        ? "data/a2-sliced-alcove-size9-focused-four-copy-reflected-summary.ndjson"
        : null,
      substitution_claim_scope: "direct_scalar_fixed_affine_A3_alcove_cellular_only",
      substitution_noncellular_inflations_open: true,
      deeper_periodic_domains_open: !isPeriodic,
      radius_two_status: radiusTwo ? "unresolved" : null,
      radius_two_rounds: radiusTwo?.rounds ?? 0,
      radius_two_failure_clauses: radiusTwo?.clauses?.length ?? 0,
      radius_two_outer_exhausted: radiusTwo?.outer_exhausted ?? false,
      radius_two_stopped_by: radiusTwo?.stopped_by ?? null,
      radius_two_cumulative_milliseconds: radiusTwo?.cumulative_milliseconds ?? 0,
      radius_two_report: radiusTwo
        ? "data/a2-sliced-alcove-size9-focused-corona2-gcts.ndjson"
        : null
    },
    shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
  };
});

await writeFile(new URL("data/a2-sliced-alcove-size9-focused-periodic-exact8.ndjson", root),
  `${records.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
const focusedCorona = records.map(record => coronaById.get(record.id));
await writeFile(new URL("data/a2-sliced-alcove-size9-focused-corona1.ndjson", root),
  `${focusedCorona.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
await writeFile(new URL("data/a2-sliced-alcove-size9-focused-corona2-gcts.ndjson", root),
  `${radiusTwoRows.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
await writeFile(new URL("data/a2-sliced-alcove-size9-focused-three-copy-summary.ndjson", root),
  `${threeCopyRows.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
await writeFile(new URL("data/a2-sliced-alcove-size9-two-copy-census-summary.json", root),
  `${JSON.stringify({ campaigns: twoCopyCampaigns, focused_candidates: twoCopyRows }, null, 2)}\n`,
  "utf8");
await writeFile(new URL("data/a2-sliced-alcove-size9-focused-four-copy-proper-summary.ndjson", root),
  `${fourCopyRows.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
await writeFile(new URL("data/a2-sliced-alcove-size9-focused-four-copy-reflected-summary.ndjson", root),
  `${reflectedFourCopyRows.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
const source = `// Generated by scripts/build-a2-sliced-size9-catalog.mjs.\n`
  + `export const A2_SLICED_SIZE9_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-sliced-size9-candidates.js", root), source, "utf8");
console.log(JSON.stringify({ candidates: candidates.length, unresolved: unresolved.map(item => item.id), periodic: periodic.map(item => item.id) }, null, 2));
