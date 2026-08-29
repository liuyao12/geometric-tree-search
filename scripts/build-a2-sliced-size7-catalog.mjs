import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import {
  a2SlicedAlcoveVertices,
  canonicalA2SlicedAlcoves,
  makeA2SlicedAlcoveUnion
} from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readNdjson = async path => (await readFile(new URL(path, root), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const readGzipNdjson = async path => gunzipSync(await readFile(new URL(path, root)))
  .toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);

const periodicRows = await readNdjson(
  "data/a2-sliced-alcove-size7-directed-periodic-exact6.ndjson"
);
const coronaById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size7-directed-corona1.ndjson"
)).map(record => [record.id, record]));
const retainedById = new Map((await readNdjson(
  "data/a2-sliced-alcove-size7-retained-corona-extension.ndjson"
)).map(record => [record.id, record]));
const longRadiusById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size7-leads-radius2-radius3-gcts.ndjson.gz"
)).map(record => [record.id, record]));
const scale3ThreeCopyById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size7-three-cluster-scale3-reflected-leads.ndjson.gz"
)).map(record => [record.id, record]));
const scale4ThreeCopyById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size7-three-cluster-scale4-reflected-leads.ndjson.gz"
)).map(record => [record.id, record]));
const scale2FourCopyById = new Map((await readGzipNdjson(
  "data/a2-sliced-alcove-size7-four-cluster-scale2-reflected-leads.ndjson.gz"
)).map(record => [record.id, record]));

const survivorRows = periodicRows.filter(record => record.classification === "unresolved");
if (survivorRows.length !== 259) {
  throw new Error(`Expected 259 six-copy survivors, found ${survivorRows.length}`);
}

const hardRows = survivorRows.map(record => {
  const corona = coronaById.get(record.id);
  const retained = retainedById.get(record.id);
  if (!corona?.corona_z3?.replay?.verified) {
    throw new Error(`Missing verified root corona for ${record.id}`);
  }
  if (!retained) throw new Error(`Missing retained-corona result for ${record.id}`);
  return { record, corona, retained };
}).filter(({ retained }) =>
  retained.retained_corona_extension_classification === "unresolved"
);

if (hardRows.length !== 151) {
  throw new Error(`Expected 151 timeout-unresolved retained coronas, found ${hardRows.length}`);
}

// Prefer candidates whose verified first corona is large and whose exact root
// corona search itself was difficult.  This is only a benchmark priority; it
// is not evidence for tiling or aperiodicity.
const priorityScore = ({ corona, retained }) => {
  const extension = retained.retained_corona_extension;
  const coronaNodes = corona.corona_z3.exact_gcts?.nodes ?? 0;
  return extension.source_first_patch_copies * 1000
    + Math.min(coronaNodes, 25000)
    + extension.placements_considered / 10;
};

const cellFromVertices = vertices => {
  const base = [0, 1, 2].map(axis => Math.min(...vertices.map(point => point[axis])));
  const ranked = vertices.map(point => ({
    point,
    rank: point.reduce((sum, value, axis) => sum + value - base[axis], 0)
  })).sort((left, right) => left.rank - right.rank);
  const first = ranked[1].point.findIndex((value, axis) => value - base[axis] === 1);
  const second = ranked[2].point.findIndex((value, axis) =>
    value - ranked[1].point[axis] === 1);
  return { base, order: [first, second, 3 - first - second] };
};

const reflectedClassKey = alcoves => {
  const reflected = alcoves.map(alcove => cellFromVertices(
    a2SlicedAlcoveVertices(alcove).map(([x, y, z]) => [y, x, z])
  ));
  return [canonicalA2SlicedAlcoves(alcoves).key, canonicalA2SlicedAlcoves(reflected).key]
    .sort()[0];
};

const rankedRows = hardRows.sort((left, right) => priorityScore(right) - priorityScore(left)
  || left.record.id.localeCompare(right.record.id));
const hardReflectionClassCount = new Set(rankedRows.map(row =>
  reflectedClassKey(row.record.alcoves)
)).size;
const reflectedClasses = new Set();
const selected = [];
for (const row of rankedRows) {
  const classKey = reflectedClassKey(row.record.alcoves);
  if (reflectedClasses.has(classKey)) continue;
  reflectedClasses.add(classKey);
  selected.push(row);
  if (selected.length === 8) break;
}

const candidates = selected.map(({ record, corona, retained }, index) => {
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  const extension = retained.retained_corona_extension;
  const longRadius = longRadiusById.get(record.id);
  if (!longRadius) throw new Error(`Missing long radius evidence for ${record.id}`);
  const radius2 = longRadius.retained_corona_extension_classification === "radius2_witness"
    ? longRadius.retained_corona_extension : longRadius.corona2_cegar;
  if (!radius2?.replay?.verified) {
    throw new Error(`Missing replayed radius-two witness for ${record.id}`);
  }
  const radius3 = longRadius.radius3_gcts;
  const scale3ThreeCopy = scale3ThreeCopyById.get(record.id);
  const scale4ThreeCopy = scale4ThreeCopyById.get(record.id);
  const scale2FourCopy = scale2FourCopyById.get(record.id);
  for (const [scale, evidence] of [[3, scale3ThreeCopy], [4, scale4ThreeCopy]]) {
    if (!evidence
      || evidence.classification !== `no_three_copy_metatile_scalar${scale}_substitution`
      || evidence.three_copy_alcove_metatile_screen?.certified !== true
      || evidence.three_copy_alcove_metatile_screen?.parents_completed
        !== evidence.three_copy_alcove_metatile_screen?.symmetry_distinct_metatiles
    ) {
      throw new Error(`Invalid scale-${scale} three-copy certificate for ${record.id}`);
    }
  }
  if (scale2FourCopy && (
    scale2FourCopy.classification !== "no_four_copy_metatile_scalar2_substitution"
    || scale2FourCopy.four_copy_alcove_metatile_screen?.certified !== true
    || scale2FourCopy.four_copy_alcove_metatile_screen?.parents_completed
      !== scale2FourCopy.four_copy_alcove_metatile_screen?.symmetry_distinct_metatiles
  )) {
    throw new Error(`Invalid scale-two four-copy certificate for ${record.id}`);
  }
  return {
    id: record.id,
    kind: "a2_sliced_alcove_census",
    registry_id: `a2_sliced_${record.id.slice("a2sa_".length)}`,
    name: `A2 Consecutive-Layer Candidate ${record.id.slice("a2sa_7_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: index + 1,
    survivor_count: selected.length,
    description: "Seven-alcove non-polycube lattice function coupling consecutive triangular sections x+y+z=k.",
    screening: {
      status: "inconclusive",
      certificate: null,
      census_stage: "a2_sliced_size7_consecutive_layers_exact_through6_2026_08_28",
      source_pool_size: 1112,
      six_copy_periodic_certificates: 853,
      six_copy_periodic_survivors: 259,
      retained_corona_timeout_survivors: 151,
      retained_corona_timeout_reflection_classes: hardReflectionClassCount,
      periodic_exact_through: 6,
      periodic_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_six_copy_hnf_visited: record.periodic_z3.hnf_visited,
      periodic_six_copy_hnf_total: record.periodic_z3.hnf_total,
      periodic_six_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_six_copy_complete: record.periodic_z3.hnf_range_exhausted === true,
      periodic_report: "data/a2-sliced-alcove-size7-directed-periodic-exact6.ndjson",
      corona_completed_radius: 2,
      corona_completed_verified: true,
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_placements_considered: corona.corona_z3.placements_considered,
      corona_search_nodes: corona.corona_z3.exact_gcts?.nodes ?? null,
      corona_report: "data/a2-sliced-alcove-size7-directed-corona1.ndjson",
      retained_corona_extension_status: retained.retained_corona_extension_classification,
      retained_corona_extension_stopped_by: extension.stopped_by,
      retained_corona_extension_placements_considered: extension.placements_considered,
      retained_corona_extension_milliseconds: extension.milliseconds,
      retained_corona_extension_report: "data/a2-sliced-alcove-size7-retained-corona-extension.ndjson",
      radius_two_patch_copies: radius2.replay.patch_copies,
      radius_two_target_points: radius2.replay.target_points,
      radius_two_occupied_points: radius2.replay.occupied_points,
      radius_two_report: "data/a2-sliced-alcove-size7-leads-radius2-radius3-gcts.ndjson.gz",
      radius_three_status: longRadius.radius3_gcts_classification,
      radius_three_failure_clauses: radius3.radius2_failure_clauses.length,
      radius_three_first_corona_clauses: radius3.first_corona_failure_clauses.length,
      radius_three_stopped_by: radius3.stopped_by,
      radius_three_cumulative_milliseconds: radius3.cumulative_milliseconds ?? radius3.milliseconds,
      radius_three_report: "data/a2-sliced-alcove-size7-leads-radius2-radius3-gcts.ndjson.gz",
      direct_scalar_substitution_scales_exhausted: [2, 3, 4, 5, 6, 7, 8],
      direct_scalar_substitution_symmetry_models: ["proper", "reflected"],
      two_copy_metatile_substitution_scales_exhausted: [2, 3],
      two_copy_metatile_substitution_symmetry_models: ["proper", "reflected"],
      three_copy_metatile_substitution_scales_exhausted: [2, 3, 4],
      three_copy_metatile_substitution_symmetry_models: ["proper", "reflected"],
      three_copy_metatile_scale3_reflected_status: scale3ThreeCopy?.classification ?? "unresolved",
      three_copy_metatile_scale3_reflected_parent_types:
        scale3ThreeCopy?.three_copy_alcove_metatile_screen?.parents_completed ?? 0,
      three_copy_metatile_scale3_reflected_report: scale3ThreeCopy
        ? "data/a2-sliced-alcove-size7-three-cluster-scale3-reflected-leads.ndjson.gz"
        : null,
      three_copy_metatile_scale4_reflected_status: scale4ThreeCopy.classification,
      three_copy_metatile_scale4_reflected_parent_types:
        scale4ThreeCopy.three_copy_alcove_metatile_screen.parents_completed,
      three_copy_metatile_scale4_reflected_report:
        "data/a2-sliced-alcove-size7-three-cluster-scale4-reflected-leads.ndjson.gz",
      four_copy_metatile_substitution_scales_exhausted: scale2FourCopy ? [2] : [],
      four_copy_metatile_scale2_reflected_status:
        scale2FourCopy?.classification ?? "unresolved",
      four_copy_metatile_scale2_reflected_parent_types:
        scale2FourCopy?.four_copy_alcove_metatile_screen?.parents_completed ?? 0,
      four_copy_metatile_scale2_reflected_report: scale2FourCopy
        ? "data/a2-sliced-alcove-size7-four-cluster-scale2-reflected-leads.ndjson.gz"
        : null
    },
    shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
  };
});

const source = `// Generated by scripts/build-a2-sliced-size7-catalog.mjs.\n`
  + `export const A2_SLICED_SIZE7_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-sliced-size7-candidates.js", root), source, "utf8");
console.log(JSON.stringify({
  candidates: candidates.length,
  timeout_unresolved_pool: hardRows.length,
  reflection_classes: hardReflectionClassCount,
  ids: candidates.map(candidate => candidate.id)
}, null, 2));
