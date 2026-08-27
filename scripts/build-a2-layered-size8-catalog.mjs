import { readFile, writeFile } from "node:fs/promises";
import { makeA2LayeredPolyprism } from "../assets/a2-layered-polyprisms.js";

const root = new URL("../", import.meta.url);
const rows = (await readFile(new URL(
  "data/a2-layered-size8-essential-periodic-exact6.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const coronaById = new Map((await readFile(new URL(
  "data/a2-layered-size8-essential-corona1-verified.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse)
  .map(record => [record.id, record]));
const corona2ById = new Map((await readFile(new URL(
  "data/a2-layered-size8-corona2-gcts-long.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse)
  .map(record => [record.id, record]));
const substitutionRows = (await readFile(new URL(
  "data/a2-layered-size8-substitution-screen-summary.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const substitutionsById = Map.groupBy
  ? Map.groupBy(substitutionRows, record => record.id)
  : substitutionRows.reduce((groups, record) => {
      const records = groups.get(record.id) ?? [];
      records.push(record);
      groups.set(record.id, records);
      return groups;
    }, new Map());

const candidates = rows
  .filter(record => record.classification === "unresolved")
  .sort((left, right) =>
    right.morphology.layer_count - left.morphology.layer_count
    || right.morphology.distinct_cross_sections - left.morphology.distinct_cross_sections
    || left.id.localeCompare(right.id)
  )
  .map((record, index, selected) => {
    const geometry = makeA2LayeredPolyprism(record.cells);
    const corona = coronaById.get(record.id);
    const corona2 = corona2ById.get(record.id)?.corona2_core_cegar;
    const substitutionEvidence = substitutionsById.get(record.id) ?? [];
    const direct = substitutionEvidence.filter(item => item.substitution);
    const twoCopy = substitutionEvidence.filter(item => item.two_copy_metatile_screen);
    const threeCopy = substitutionEvidence.filter(item => item.three_copy_metatile_screen);
    const directScales = [...new Set(direct
      .filter(item => item.substitution.inflation_kind === "scalar")
      .map(item => item.substitution.scale))].sort((a, b) => a - b);
    const directLayerScalePairs = direct.map(item => [
      item.substitution.eisenstein_multiplier?.a,
      item.substitution.vertical_scale
    ]).filter(pair => pair.every(Number.isInteger));
    const twoCopyScales = [...new Set(twoCopy.map(item =>
      item.two_copy_metatile_screen.scale))].sort((a, b) => a - b);
    const threeCopyScales = [...new Set(threeCopy
      .filter(item => item.three_copy_metatile_screen.certified)
      .map(item => item.three_copy_metatile_screen.scale))].sort((a, b) => a - b);
    const threeCopyTypesByScale = Object.fromEntries(threeCopy.map(item => [
      item.three_copy_metatile_screen.scale,
      item.three_copy_metatile_screen.symmetry_distinct_metatiles
    ]));
    return {
      id: record.id,
      kind: "a2_layered_polyprism_census",
      registry_id: `a2_layered_${record.id.slice("a2lp_".length)}`,
      name: `A2 Layer-Essential Candidate ${record.id.slice("a2lp_8_".length)}`,
      cells: record.cells,
      morphology: record.morphology,
      lattice_points: geometry.occ.length,
      survivor_priority: index + 1,
      survivor_count: selected.length,
      description: "Size-eight non-product A2-layer lattice function whose cross-section changes across at least three x+y+z slabs.",
      screening: {
        status: "inconclusive",
        certificate: null,
        census_stage: "a2_layered_size8_layer_essential_exact_through6_2026_08_27",
        source_pool_size: 4940,
        periodic_one_copy_certificates: 4529,
        periodic_two_copy_certificates_after_one_copy_screen: 405,
        periodic_four_copy_certificates_after_three_copy_screen: 2,
        periodic_exact_through: 6,
        periodic_solver_unknowns: 0,
        periodic_hnf_bases_exhausted_by_copies: {
          1: 35, 2: 155, 3: 455, 4: 651, 5: 1085, 6: 2015
        },
        periodic_six_copy_exact_multicover_nodes:
          record.periodic_z3.exact_multicover_nodes ?? 0,
        periodic_six_copy_exact_failed_states:
          record.periodic_z3.exact_multicover_failed_states ?? 0,
        periodic_six_copy_complete:
          record.periodic_z3.hnf_range_exhausted === true
          && record.periodic_z3.hnf_visited === 2015
          && record.periodic_z3.solver_unknown === 0,
        periodic_report: "data/a2-layered-size8-essential-periodic-exact6.ndjson",
        corona_completed_radius: corona?.corona_z3?.replay?.verified ? 1 : 0,
        corona_completed_verified: corona?.corona_z3?.replay?.verified ?? false,
        corona_root_patch_copies: corona?.corona_z3?.replay?.patch_copies ?? null,
        corona_solver_timeout_ms: corona?.corona_z3?.stopped_by === "solver_timeout"
          ? corona.corona_z3.milliseconds : null,
        corona_report: "data/a2-layered-size8-essential-corona1-verified.ndjson",
        corona2_gcts_rounds: corona2?.rounds ?? 0,
        corona2_gcts_sound_clauses: corona2?.clauses?.length ?? 0,
        corona2_gcts_outer_exhausted: corona2?.outer_exhausted ?? false,
        corona2_gcts_stopped_by: corona2?.stopped_by ?? null,
        corona2_gcts_cumulative_milliseconds: corona2?.cumulative_milliseconds ?? 0,
        corona2_report: "data/a2-layered-size8-corona2-gcts-long.ndjson",
        direct_scalar_substitution_scales_exhausted: directScales,
        direct_layer_scale_pairs_exhausted: directLayerScalePairs.length,
        direct_layer_scale_pair_range: [2, 8],
        two_copy_metatile_substitution_scales_exhausted: twoCopyScales,
        three_copy_metatile_substitution_scales_exhausted: threeCopyScales,
        three_copy_metatile_types_exhausted_by_scale: threeCopyTypesByScale,
        substitution_report: "data/a2-layered-size8-substitution-screen-summary.ndjson"
      },
      shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
    };
  });

const source = `// Generated by scripts/build-a2-layered-size8-catalog.mjs.\n`
  + `export const A2_LAYERED_SIZE8_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-layered-size8-candidates.js", root), source, "utf8");
console.log(JSON.stringify({ candidates: candidates.length, ids: candidates.map(item => item.id) }, null, 2));
