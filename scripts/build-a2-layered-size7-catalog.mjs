import { readFile, writeFile } from "node:fs/promises";
import { makeA2LayeredPolyprism } from "../assets/a2-layered-polyprisms.js";

const root = new URL("../", import.meta.url);
const readNdjson = async path => (await readFile(new URL(path, root), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const throughFour = await readNdjson("data/a2-layered-size7-periodic-z3-through4.ndjson");
const coronaOne = await readNdjson("data/a2-layered-size7-corona1-z3.ndjson");
const focused = await readNdjson("data/a2-layered-size7-corona2-focused.ndjson");
const deep = await readNdjson("data/a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson");
const coreLong = await readNdjson("data/a2-layered-size7-corona2-core-a2lp_7_00232-long.ndjson");
const coreExtended = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-corona2-core-a2lp_7_${id}-extended.ndjson`)))).flat();
const coreDeeper = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-corona2-core-a2lp_7_${id}-deeper.ndjson`)))).flat();
const coreStrengthened = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-corona2-core-a2lp_7_${id}-strengthened.ndjson`)))).flat();
const coreLonger128 = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-corona2-core-a2lp_7_${id}-longer128.ndjson`)))).flat();
const minimizedCores = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-corona2-core-a2lp_7_${id}-mincore.ndjson`)))).flat();
const periodicSixToEight = (await Promise.all([1, 2, 3].map(part =>
  readNdjson(`data/a2-layered-size7-periodic-z3-focus6to8-part${part}.ndjson`)
))).flat();
const periodicExactSix = (await Promise.all([
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
].map(id => readNdjson(`data/a2-layered-size7-periodic-exact6-a2lp_7_${id}.ndjson`)))).flat();
const substitutions = new Map();
for (const scale of [2, 3, 4, 5, 6]) {
  for (const record of await readNdjson(`data/a2-layered-size7-substitution-scale${scale}-focused.ndjson`)) {
    if (!substitutions.has(record.id)) substitutions.set(record.id, []);
    substitutions.get(record.id).push(record);
  }
}
const anisotropicSubstitutions = await readNdjson(
  "data/a2-layered-size7-substitution-anisotropic-s2to8-focused.ndjson"
);
const twoClusterSubstitutions = new Map();
for (const scale of [2, 3]) {
  for (const record of await readNdjson(
    `data/a2-layered-size7-two-cluster-substitution-scalar${scale}-focused.ndjson`
  )) {
    if (!twoClusterSubstitutions.has(record.id)) twoClusterSubstitutions.set(record.id, []);
    twoClusterSubstitutions.get(record.id).push(record);
  }
}
const threeClusterSubstitutions = new Map();
for (const scale of [2, 3]) {
  for (const id of [
    "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
  ]) {
    const records = await readNdjson(
      `data/a2-layered-size7-three-cluster-substitution-scalar${scale}-a2lp_7_${id}.ndjson`
    );
    const catalogRecord = { ...records[0], catalog_scale: scale };
    if (!threeClusterSubstitutions.has(catalogRecord.id)) {
      threeClusterSubstitutions.set(catalogRecord.id, []);
    }
    threeClusterSubstitutions.get(catalogRecord.id).push(catalogRecord);
  }
}
const fourClusterEnumerations = new Map();
const fourClusterSubstitutions = new Map();
for (const id of [
  "00128", "00211", "00232", "00235", "00694", "00755", "00777", "00809"
]) {
  const enumeration = await readNdjson(
    `data/a2-layered-size7-four-cluster-enumeration-a2lp_7_${id}.ndjson`
  );
  const substitution = await readNdjson(
    `data/a2-layered-size7-four-cluster-substitution-scalar2-a2lp_7_${id}.ndjson`
  );
  fourClusterEnumerations.set(enumeration[0].id, enumeration[0]);
  fourClusterSubstitutions.set(substitution[0].id, substitution[0]);
}
const anisotropicById = new Map();
for (const record of anisotropicSubstitutions) {
  if (!anisotropicById.has(record.id)) anisotropicById.set(record.id, []);
  anisotropicById.get(record.id).push(record);
}
const byId = records => new Map(records.map(record => [record.id, record]));
const periodicById = byId(throughFour);
const coronaById = byId(coronaOne);
const focusedById = byId(focused);
const deepById = byId(deep);
const coreLongById = byId(coreLong);
const coreExtendedById = byId(coreExtended);
const coreDeeperById = byId(coreDeeper);
const coreStrengthenedById = byId(coreStrengthened);
const coreLonger128ById = byId(coreLonger128);
const minimizedCoreById = byId(minimizedCores);
const periodicSixToEightById = byId(periodicSixToEight);
const periodicExactSixById = byId(periodicExactSix);
const selected = [...focusedById.keys()].sort((left, right) =>
  coronaById.get(left).corona_z3.replay.patch_copies
  - coronaById.get(right).corona_z3.replay.patch_copies
  || left.localeCompare(right)
);
const candidates = selected.map((id, index) => {
  const periodic = periodicById.get(id);
  const corona = coronaById.get(id);
  const second = focusedById.get(id);
  const deepSecond = deepById.get(id);
  const coreSecond = coreLonger128ById.get(id) ?? coreStrengthenedById.get(id) ?? coreDeeperById.get(id)
    ?? coreExtendedById.get(id) ?? coreLongById.get(id);
  const minimizedCore = minimizedCoreById.get(id);
  const largerPeriodic = periodicSixToEightById.get(id);
  const exactSix = periodicExactSixById.get(id);
  const substitutionScreens = substitutions.get(id) ?? [];
  const anisotropicScreens = anisotropicById.get(id) ?? [];
  const twoClusterScreens = twoClusterSubstitutions.get(id) ?? [];
  const threeClusterScreens = threeClusterSubstitutions.get(id) ?? [];
  const fourClusterEnumeration = fourClusterEnumerations.get(id);
  const fourClusterScreen = fourClusterSubstitutions.get(id);
  const corona2States = Math.max(
    second.corona2_cegar.first_coronas_rejected,
    deepSecond?.corona2_cegar?.first_coronas_rejected ?? 0
  );
  const geometry = makeA2LayeredPolyprism(periodic.cells);
  return {
    id,
    kind: "a2_layered_polyprism_census",
    registry_id: `a2_layered_${id.slice("a2lp_".length)}`,
    name: `A2 Layered Candidate ${id.slice("a2lp_7_".length)}`,
    cells: periodic.cells,
    lattice_points: geometry.occ.length,
    survivor_priority: index + 1,
    survivor_count: selected.length,
    description: "Size-seven non-product A2-layer lattice function retained after exact weighted quotient and focused second-corona screening.",
    screening: {
      status: "inconclusive",
      certificate: null,
      census_stage: "a2_layered_size7_exact_through6_2026_08_27",
      source_pool_size: 1119,
      periodic_two_copy_certificates: 910,
      periodic_four_copy_certificates_after_two_copy_screen: 98,
      periodic_exact_through: 6,
      periodic_determinant14_hnf_bases_exhausted: 399,
      periodic_solver_unknowns: 0,
      corona_completed_radius: 1,
      corona_completed_verified: true,
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_root_placements_considered: corona.corona_z3.placements_considered,
      corona2_first_states_checked: corona2States,
      corona2_first_states_rejected: corona2States,
      corona2_outer_exhausted: deepSecond?.corona2_cegar?.outer_exhausted
        ?? second.corona2_cegar.outer_exhausted,
      corona2_gcts_sound_clauses: coreSecond?.corona2_core_cegar?.clauses?.length ?? 0,
      corona2_gcts_rounds: coreSecond?.corona2_core_cegar?.rounds ?? 0,
      corona2_gcts_continuation_rounds:
        coreSecond?.corona2_core_cegar?.continuation_rounds ?? 0,
      corona2_gcts_milliseconds:
        coreSecond?.corona2_core_cegar?.cumulative_milliseconds
          ?? coreSecond?.corona2_core_cegar?.milliseconds ?? 0,
      corona2_gcts_smallest_certified_core: minimizedCore?.reduced_outer_placement_indices?.length ?? null,
      corona2_gcts_minimized_core_report: minimizedCore
        ? `data/a2-layered-size7-corona2-core-${id}-mincore.ndjson`
        : null,
      periodic_six_copy_hnf_total: 741,
      periodic_six_copy_hnf_visited: exactSix?.periodic_z3?.hnf_visited ?? 0,
      periodic_six_copy_solver_unknowns: exactSix?.periodic_z3?.solver_unknown ?? 0,
      periodic_six_copy_complete: exactSix?.periodic_z3?.exhausted_by_copies?.["6"] === 741,
      periodic_six_copy_exact_multicover_nodes:
        exactSix?.periodic_z3?.exact_multicover_nodes ?? 0,
      periodic_six_copy_exact_failed_states:
        exactSix?.periodic_z3?.exact_multicover_failed_states ?? 0,
      substitution_scalar_scales_excluded: substitutionScreens
        .filter(record => record.substitution_classification === "no_scalar_substitution_at_scale")
        .map(record => record.substitution.scale).sort((left, right) => left - right),
      substitution_rule_found: substitutionScreens.some(record =>
        record.substitution_classification === "scalar_substitution_rule"
      ) || anisotropicScreens.some(record =>
        record.substitution_classification === "lattice_substitution_rule"
      ) || twoClusterScreens.some(record =>
        record.classification === "two_copy_metatile_substitution_system"
      ) || threeClusterScreens.some(record =>
        record.classification === "three_copy_metatile_substitution_system"
      ) || fourClusterScreen?.classification === "four_copy_metatile_substitution_system",
      substitution_anisotropic_scale_range: [2, 8],
      substitution_anisotropic_inflations_excluded: anisotropicScreens.filter(record =>
        record.substitution_classification === "no_lattice_substitution_for_inflation"
      ).length,
      substitution_two_copy_metatile_types: twoClusterScreens[0]
        ?.two_copy_metatile_screen?.symmetry_distinct_metatiles ?? 0,
      substitution_two_copy_metatile_scalar_scales_excluded: twoClusterScreens
        .filter(record => record.mixed_two_copy_metatile_screen?.certified)
        .map(record => record.mixed_two_copy_metatile_screen.scale)
        .sort((left, right) => left - right),
      substitution_two_copy_metatile_parent_cases_excluded: twoClusterScreens.reduce(
        (total, record) => total + (record.mixed_two_copy_metatile_screen?.metatile_types ?? 0), 0
      ),
      substitution_three_copy_metatile_types:
        threeClusterScreens[0]?.three_copy_metatile_screen?.symmetry_distinct_metatiles ?? 0,
      substitution_three_copy_metatile_scalar_scales_excluded: threeClusterScreens
        .filter(record => record.three_copy_metatile_screen?.certified)
        .map(record => record.catalog_scale)
        .sort((left, right) => left - right),
      substitution_three_copy_metatile_exact_unsat_parents_by_scale: Object.fromEntries(
        threeClusterScreens.map(record => [
          record.catalog_scale,
          record.three_copy_metatile_screen.parent_counts?.exact_unsat ?? 0
        ])
      ),
      substitution_four_copy_metatile_types:
        fourClusterScreen?.four_copy_metatile_screen?.symmetry_distinct_metatiles ?? 0,
      substitution_four_copy_metatile_scalar_scales_excluded:
        fourClusterScreen?.four_copy_metatile_screen?.certified ? [2] : [],
      substitution_four_copy_metatile_local_obstruction_parents:
        fourClusterScreen?.four_copy_metatile_screen?.parent_counts?.local_obstruction ?? 0,
      substitution_four_copy_metatile_exact_unsat_parents:
        fourClusterScreen?.four_copy_metatile_screen?.parent_counts?.exact_unsat ?? 0,
      periodic_report: "data/a2-layered-size7-periodic-z3-through4.ndjson",
      corona_report: "data/a2-layered-size7-corona1-z3.ndjson",
      corona2_report: deepSecond
        ? "data/a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson"
        : "data/a2-layered-size7-corona2-focused.ndjson",
      corona2_gcts_report: coreSecond
        ? `data/a2-layered-size7-corona2-core-${id}-longer128.ndjson`
        : null,
      periodic_larger_report: exactSix
        ? `data/a2-layered-size7-periodic-exact6-${id}.ndjson`
        : largerPeriodic
          ? "data/a2-layered-size7-periodic-z3-focus6to8-part*.ndjson"
          : null,
      substitution_reports: substitutionScreens.map(record =>
        `data/a2-layered-size7-substitution-scale${record.substitution.scale}-focused.ndjson`
      ),
      substitution_anisotropic_report: anisotropicScreens.length
        ? "data/a2-layered-size7-substitution-anisotropic-s2to8-focused.ndjson"
        : null,
      substitution_two_copy_metatile_reports: twoClusterScreens.map(record =>
        `data/a2-layered-size7-two-cluster-substitution-scalar${record.mixed_two_copy_metatile_screen.scale}-focused.ndjson`
      ),
      substitution_three_copy_metatile_reports: threeClusterScreens.map(record =>
        `data/a2-layered-size7-three-cluster-substitution-scalar${record.catalog_scale}-${id}.ndjson`
      ),
      substitution_four_copy_metatile_enumeration_report: fourClusterEnumeration
        ? `data/a2-layered-size7-four-cluster-enumeration-${id}.ndjson`
        : null,
      substitution_four_copy_metatile_report: fourClusterScreen
        ? `data/a2-layered-size7-four-cluster-substitution-scalar2-${id}.ndjson`
        : null
    },
    shell_screening: { robust_completed_shell: 0, deepest_completed_shell: 0 }
  };
});
const source = `// Generated by scripts/build-a2-layered-size7-catalog.mjs.\n`
  + `export const A2_LAYERED_SIZE7_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`;
await writeFile(new URL("assets/a2-layered-size7-candidates.js", root), source, "utf8");
console.log(JSON.stringify({ candidates: candidates.length, ids: selected }, null, 2));
