import { readFile, writeFile } from "node:fs/promises";
import { makeA2LayeredPolyprism } from "../assets/a2-layered-polyprisms.js";

const root = new URL("../", import.meta.url);
const periodicRows = (await readFile(new URL(
  "data/a2-layered-size9-directed-periodic-exact6.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const coronaById = new Map((await readFile(new URL(
  "data/a2-layered-size9-directed-focus-corona1.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse)
  .map(record => [record.id, record]));
const corona2ById = new Map((await readFile(new URL(
  "data/a2-layered-size9-directed-corona2-gcts.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse)
  .map(record => [record.id, record]));
const directRows = (await readFile(new URL(
  "data/a2-layered-size9-directed-substitution-direct-s2to8.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const twoCopyRows = (await readFile(new URL(
  "data/a2-layered-size9-directed-substitution-two-copy-s2to3.ndjson", root
), "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const directById = Map.groupBy(directRows, record => record.id);
const twoCopyById = Map.groupBy(twoCopyRows, record => record.id);
const partialThree = JSON.parse((await readFile(new URL(
  "data/a2-layered-size9-directed-three-copy-scalar2-a2lp_9_00000-partial500.ndjson", root
), "utf8")).trim());

const candidates = periodicRows
  .filter(record => record.classification === "unresolved")
  .map((record, index, selected) => {
    const corona = coronaById.get(record.id);
    const corona2 = corona2ById.get(record.id)?.corona2_core_cegar;
    const direct = directById.get(record.id) ?? [];
    const twoCopy = twoCopyById.get(record.id) ?? [];
    if (!corona?.corona_z3?.replay?.verified) {
      throw new Error(`Missing verified root corona for ${record.id}`);
    }
    const geometry = makeA2LayeredPolyprism(record.cells);
    return {
      id: record.id,
      kind: "a2_layered_polyprism_census",
      registry_id: `a2_layered_${record.id.slice("a2lp_".length)}`,
      name: `A2 Directed-Layer Candidate ${record.id.slice("a2lp_9_".length)}`,
      cells: record.cells,
      morphology: record.morphology,
      lattice_points: geometry.occ.length,
      survivor_priority: index + 1,
      survivor_count: selected.length,
      description: "Size-nine A2-layer lattice function spanning five x+y+z slabs, with a distinct cross-section in every slab and a directed transverse profile.",
      screening: {
        status: "inconclusive",
        certificate: null,
        census_stage: "a2_layered_size9_directed_exact_through6_2026_08_27",
        source_pool_size: 724,
        periodic_two_copy_certificates: 430,
        periodic_two_copy_survivors: 294,
        periodic_four_copy_focus_checked: periodicRows.length,
        periodic_four_copy_focus_certificates: periodicRows
          .filter(item => item.classification === "periodic").length,
        periodic_exact_through: 6,
        periodic_solver_unknowns: record.periodic_z3.solver_unknown,
        periodic_six_copy_orbit_representatives_visited: record.periodic_z3.hnf_visited,
        periodic_six_copy_orbit_representatives_total: record.periodic_z3.hnf_orbit_total,
        periodic_six_copy_hnf_covered: record.periodic_z3.hnf_covered,
        periodic_six_copy_hnf_total: record.periodic_z3.hnf_total,
        periodic_six_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
        periodic_six_copy_complete: record.periodic_z3.hnf_range_exhausted === true,
        periodic_report: "data/a2-layered-size9-directed-periodic-exact6.ndjson",
        corona_completed_radius: 1,
        corona_completed_verified: true,
        corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
        corona_placements_considered: corona.corona_z3.placements_considered,
        corona_search_nodes: corona.corona_z3.exact_gcts?.nodes ?? null,
        corona_report: "data/a2-layered-size9-directed-focus-corona1.ndjson",
        corona2_gcts_rounds: corona2?.rounds ?? 0,
        corona2_gcts_sound_clauses: corona2?.clauses?.length ?? 0,
        corona2_gcts_outer_exhausted: corona2?.outer_exhausted ?? false,
        corona2_gcts_stopped_by: corona2?.stopped_by ?? null,
        corona2_gcts_cumulative_milliseconds: corona2?.cumulative_milliseconds ?? 0,
        corona2_report: "data/a2-layered-size9-directed-corona2-gcts.ndjson",
        direct_layer_scale_pairs_exhausted: direct.length,
        direct_layer_scale_pair_range: [2, 8],
        two_copy_metatile_substitution_scales_exhausted: twoCopy
          .map(item => item.two_copy_metatile_screen.scale).sort((a, b) => a - b),
        two_copy_metatile_types_exhausted_by_scale: Object.fromEntries(twoCopy.map(item => [
          item.two_copy_metatile_screen.scale,
          item.two_copy_metatile_screen.symmetry_distinct_metatiles
        ])),
        three_copy_metatile_scale2_partial_parents: record.id === partialThree.id
          ? partialThree.three_copy_metatile_screen.parents_completed : 0,
        three_copy_metatile_scale2_types: record.id === partialThree.id
          ? partialThree.three_copy_metatile_screen.symmetry_distinct_metatiles : null,
        substitution_direct_report: "data/a2-layered-size9-directed-substitution-direct-s2to8.ndjson",
        substitution_two_copy_report: "data/a2-layered-size9-directed-substitution-two-copy-s2to3.ndjson"
      },
      shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
    };
  });

const source = `// Generated by scripts/build-a2-layered-size9-catalog.mjs.\n`
  + `export const A2_LAYERED_SIZE9_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-layered-size9-candidates.js", root), source, "utf8");
console.log(JSON.stringify({ candidates: candidates.length, ids: candidates.map(item => item.id) }, null, 2));
