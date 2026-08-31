#!/usr/bin/env node
/** Build the leading candidates recovered from the complete size-nine census. */

import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readGzipNdjson = async relativePath => gunzipSync(
  await readFile(new URL(relativePath, root))
).toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
const readJson = async relativePath => JSON.parse(await readFile(new URL(relativePath, root), "utf8"));

const exactEight = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-periodic-exact8-complete.ndjson.gz"
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
const twoCopySubstitutions = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-two-copy-substitution-scale2to3.ndjson.gz"
);
const threeCopySubstitutions = [
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-three-copy-substitution-scale2.ndjson.gz"
  )),
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-three-copy-substitution-scale3-04636.ndjson.gz"
  )),
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-three-copy-substitution-scale3-additional-leaders.ndjson.gz"
  ))
];
const fourCopySubstitutions = [
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-four-copy-substitution-scale2-proper-leaders.ndjson.gz"
  )),
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-four-copy-substitution-scale2-reflected-leaders.ndjson.gz"
  ))
];
const periodicClusterSubstitutions = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-periodic-cluster-substitutions.ndjson.gz"
);
const tenCopySummary = await readJson(
  "data/a2-sliced-size9-palindromic-periodic10-exact10m-summary.json"
);
const tenCopyReceipts = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-periodic10-best10m-receipts.ndjson.gz"
);
const radiusTwoContinuations = await readGzipNdjson(
  "data/a2-sliced-size9-palindromic-corona2-core256.ndjson.gz"
);
const fiveCopySummary04468 = await readJson(
  "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-04468-summary.json"
);
const fiveCopySummaryReflected04636 = await readJson(
  "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-04636-summary.json"
);
const fiveCopyGeometryReplayReflected04636 = await readJson(
  "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-04636-geometric-replay.json"
);
const fiveCopySummaryReflected01085 = await readJson(
  "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-01085-summary.json"
);
const fiveCopyGeometryReplayReflected01085 = await readJson(
  "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-01085-geometric-replay.json"
);
const normalizedFiveCopySummary = summary => ({
  id: summary.id,
  classification: summary.classification,
  five_copy_alcove_metatile_screen: {
    certified: summary.certified,
    scale: summary.scale,
    include_reflections: summary.include_reflections,
    family: summary.family,
    four_copy_parent_total: summary.four_copy_parent_total,
    raw_connected_extensions: summary.raw_connected_extensions,
    symmetry_distinct_metatiles: summary.symmetry_distinct_metatiles,
    canonical_sha256: summary.canonical_sha256,
    parents_completed: summary.parents_completed,
    parent_counts: summary.parent_counts,
    closed_alphabet: summary.closed_alphabet,
    all_parent_replays_verified: summary.all_parent_replays_verified,
    parent_results_sha256: summary.parent_results_sha256,
    archive_sha256: summary.archive_sha256,
  }
});
const fiveCopySubstitutions = [
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-04636.ndjson.gz"
  )),
  ...(await readGzipNdjson(
    "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-01085.ndjson.gz"
  )),
  normalizedFiveCopySummary(fiveCopySummary04468),
  normalizedFiveCopySummary(fiveCopySummaryReflected04636),
  normalizedFiveCopySummary(fiveCopySummaryReflected01085)
];
const tenCopySolverProbe = tenCopySummary.solver_probe;
if (!tenCopySolverProbe
    || tenCopySolverProbe.solver !== "qffd"
    || tenCopySolverProbe.timeout_ms_per_orbit !== 120000
    || tenCopySolverProbe.completed_shards !== 18
    || tenCopySolverProbe.partial_interrupted_receipts_excluded !== 12
    || tenCopySolverProbe.periodic_certificates !== 0
    || tenCopySolverProbe.exact_negative_orbits !== 0
    || tenCopySolverProbe.solver_unknown_shards !== 18) {
  throw new Error("Missing validated alternate-solver ten-copy probe");
}
const coronaOverrides = [
  ...(await readGzipNdjson("data/a2-sliced-size9-palindromic-corona-z3-04636.ndjson.gz")),
  ...(await readGzipNdjson("data/a2-sliced-size9-palindromic-corona-z3-04468.ndjson.gz"))
];
const coronaById = new Map(exactCorona.map(record => [record.id, record]));
for (const record of coronaOverrides) coronaById.set(record.id, record);

const selectedIds = [
  "a2sp_9_04636", "a2sp_9_01085", "a2sp_9_04468",
  "a2sp_9_15353", "a2sp_9_17745"
];
const periodicById = new Map(exactEight.map(record => [record.id, record]));
const exactSixById = new Map(exactSix.map(record => [record.id, record]));
const clusterSubstitutionById = new Map(periodicClusterSubstitutions.map(record => [record.id, record]));
const tenCopySummaryById = new Map(tenCopySummary.candidates.map(record => [record.id, record]));
const radiusTwoById = new Map(radiusTwoContinuations.map(record => [record.id, record]));
const fiveCopySubstitutionById = fiveCopySubstitutions.reduce((groups, record) => {
  const rows = groups.get(record.id) ?? [];
  rows.push(record);
  groups.set(record.id, rows);
  return groups;
}, new Map());
const tenCopyReceiptsById = tenCopyReceipts.reduce((groups, record) => {
  const rows = groups.get(record.id) ?? [];
  rows.push(record);
  groups.set(record.id, rows);
  return groups;
}, new Map());
const fourCopySubstitutionById = fourCopySubstitutions.reduce((groups, record) => {
  const rows = groups.get(record.id) ?? [];
  rows.push(record);
  groups.set(record.id, rows);
  return groups;
}, new Map());
const directSubstitutionById = Map.groupBy
  ? Map.groupBy(directSubstitutions, record => record.id)
  : directSubstitutions.reduce((groups, record) => {
      const rows = groups.get(record.id) ?? [];
      rows.push(record);
      groups.set(record.id, rows);
      return groups;
    }, new Map());
const twoCopySubstitutionById = twoCopySubstitutions.reduce((groups, record) => {
  const rows = groups.get(record.id) ?? [];
  rows.push(record);
  groups.set(record.id, rows);
  return groups;
}, new Map());
const threeCopySubstitutionById = threeCopySubstitutions.reduce((groups, record) => {
  const rows = groups.get(record.id) ?? [];
  rows.push(record);
  groups.set(record.id, rows);
  return groups;
}, new Map());

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
  const orientationHashes = proofOrientationTransforms.map(([sign, permutation], orientationIndex) => {
    const shift = shifts[orientationIndex];
    const transform = point => [0, 1, 2].map(axis =>
      sign * point[permutation[axis]] - shift[axis]
    );
    const vertices = geometry.v.map(transform).map(point => point.join(",")).sort().join("|");
    const occupancy = geometry.occ.map(([point, weight]) =>
      `${transform(point).join(",")}:${weight}`
    ).sort().join("|");
    return `${vertices}@@${occupancy}`;
  });
  // Prototile3D visits these proof transforms in this order, then folds tile
  // stabilizers. Mapping by the full weighted geometry also handles the
  // three-orientation stabilizer of candidate 17745.
  const webVisitOrder = [0, 3, 4, 1, 2, 5];
  const webHashes = [];
  for (const proofIndex of webVisitOrder) {
    if (!webHashes.includes(orientationHashes[proofIndex])) {
      webHashes.push(orientationHashes[proofIndex]);
    }
  }
  const proofToWebOrientation = orientationHashes.map(hash => webHashes.indexOf(hash));
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
const candidates = selectedIds.map((id, index) => {
  const record = periodicById.get(id);
  const sixCopy = exactSixById.get(id);
  const corona = coronaById.get(id);
  const direct = directSubstitutionById.get(id) ?? [];
  const twoCopy = twoCopySubstitutionById.get(id) ?? [];
  const threeCopy = threeCopySubstitutionById.get(id) ?? [];
  const fourCopy = fourCopySubstitutionById.get(id) ?? [];
  const tenCopy = tenCopySummaryById.get(id) ?? null;
  const tenCopyComplete = tenCopy?.node_capped_orbits === 0;
  const radiusTwo = radiusTwoById.get(id) ?? null;
  const fiveCopies = fiveCopySubstitutionById.get(id) ?? [];
  const fiveCopy = fiveCopies.find(result =>
    result.five_copy_alcove_metatile_screen.include_reflections === false) ?? null;
  const reflectedFiveCopy = fiveCopies.find(result =>
    result.five_copy_alcove_metatile_screen.include_reflections === true) ?? null;
  if (!record || !sixCopy || !corona) throw new Error(`Missing focused receipt for ${id}`);
  const periodicCertificate = record.periodic_z3.certificate ?? null;
  const clusterSubstitution = clusterSubstitutionById.get(id) ?? null;
  const isPeriodic = periodicCertificate !== null;
  if (isPeriodic) {
    if (record.classification !== "periodic"
        || record.periodic_z3.replay?.verified !== true
        || periodicCertificate.copies !== 8
        || clusterSubstitution?.substitution?.replay?.verified !== true) {
      throw new Error(`Missing replayed periodic/substitution certificate for ${id}`);
    }
  } else if (record.classification !== "unresolved"
      || record.periodic_z3.hnf_range_exhausted !== true
      || record.periodic_z3.hnf_covered !== 455
      || record.periodic_z3.solver_unknown !== 0) {
    throw new Error(`Expected complete eight-copy exclusion for ${id}`);
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
  if (twoCopy.length !== 4 || twoCopy.some(result =>
    !result.classification.startsWith("no_two_copy_metatile_scalar")
    || result.two_copy_alcove_metatile_screen.certified !== true)) {
    throw new Error(`Missing scale-2-and-3 two-copy substitution exclusions for ${id}`);
  }
  const expectedThreeCopyNegatives = [
    "a2sp_9_04636", "a2sp_9_01085", "a2sp_9_04468"
  ].includes(id) ? 4 : 2;
  if (threeCopy.length !== expectedThreeCopyNegatives || threeCopy.some(result =>
    !result.classification.startsWith("no_three_copy_metatile_scalar")
    || result.three_copy_alcove_metatile_screen.certified !== true)) {
    throw new Error(`Missing three-copy substitution exclusions for ${id}`);
  }
  if (!isPeriodic && (fourCopy.length !== 2 || fourCopy.some(result =>
      result.classification !== "no_four_copy_metatile_scalar2_substitution"
      || result.four_copy_alcove_metatile_screen.certified !== true))) {
    throw new Error(`Missing proper/reflected scale-2 four-copy substitution exclusions for ${id}`);
  }
  if (!isPeriodic) {
    const receipts = tenCopyReceiptsById.get(id) ?? [];
    const exactNegative = receipts.filter(result => result.periodic_z3.solver_unknown === 0);
    if (!tenCopy || tenCopySummary.copies !== 10
        || tenCopy.classification !== "bounded_inconclusive"
        || tenCopy.orbit_total !== 85
        || tenCopy.orbit_receipts !== 85
        || tenCopy.exact_negative_orbits + tenCopy.node_capped_orbits !== 85
        || receipts.length !== 85
        || exactNegative.length !== tenCopy.exact_negative_orbits
        || exactNegative.reduce((sum, result) => sum + result.periodic_z3.hnf_covered, 0)
          !== tenCopy.hnfs_exactly_excluded) {
      throw new Error(`Missing validated ten-copy bounded campaign for ${id}`);
    }
    if (!radiusTwo
        || radiusTwo.corona2_core_classification !== "unresolved"
        || radiusTwo.corona2_core_cegar.outer_exhausted !== false
        || radiusTwo.corona2_core_cegar.rounds !== 256
        || radiusTwo.corona2_core_cegar.clauses?.length !== 256
        || radiusTwo.corona2_core_cegar.stopped_by !== "round_limit") {
      throw new Error(`Missing validated radius-two continuation for ${id}`);
    }
  }
  const expectedFiveCopyParents = new Map([
    ["a2sp_9_04636", 17707],
    ["a2sp_9_01085", 68758],
    ["a2sp_9_04468", 1999910]
  ]).get(id);
  if (expectedFiveCopyParents && (
      fiveCopy?.classification !== "no_five_copy_metatile_scalar2_substitution"
      || fiveCopy.five_copy_alcove_metatile_screen.certified !== true
      || fiveCopy.five_copy_alcove_metatile_screen.include_reflections !== false
      || fiveCopy.five_copy_alcove_metatile_screen.symmetry_distinct_metatiles !== expectedFiveCopyParents
      || fiveCopy.five_copy_alcove_metatile_screen.parents_completed !== expectedFiveCopyParents
      || fiveCopy.five_copy_alcove_metatile_screen.parent_counts.atomic_local_obstruction !== expectedFiveCopyParents
      || (fiveCopy.five_copy_alcove_metatile_screen.parent_results
        ? fiveCopy.five_copy_alcove_metatile_screen.parent_results.some(result =>
          result.atomic_local_obstruction_replay?.verified !== true)
        : fiveCopy.five_copy_alcove_metatile_screen.all_parent_replays_verified !== true))) {
    throw new Error(`Missing replayed proper five-copy substitution exclusion for ${id}`);
  }
  if (id === "a2sp_9_04636" && (
      reflectedFiveCopy?.classification !== "no_five_copy_metatile_scalar2_substitution"
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.certified !== true
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.symmetry_distinct_metatiles !== 931637
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.parents_completed !== 931637
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.parent_counts.atomic_local_obstruction !== 931637
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.all_parent_replays_verified !== true
      || fiveCopyGeometryReplayReflected04636.id !== id
      || fiveCopyGeometryReplayReflected04636.parents_replayed !== 931637
      || fiveCopyGeometryReplayReflected04636.replay_failures !== 0
      || fiveCopyGeometryReplayReflected04636.canonical_sha256
        !== reflectedFiveCopy.five_copy_alcove_metatile_screen.canonical_sha256)) {
    throw new Error("Missing replayed reflected five-copy substitution exclusion for a2sp_9_04636");
  }
  if (id === "a2sp_9_01085" && (
      reflectedFiveCopy?.classification !== "no_five_copy_metatile_scalar2_substitution"
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.certified !== true
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.symmetry_distinct_metatiles !== 1109220
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.parents_completed !== 1109220
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.parent_counts.atomic_local_obstruction !== 1109220
      || reflectedFiveCopy.five_copy_alcove_metatile_screen.all_parent_replays_verified !== true
      || fiveCopyGeometryReplayReflected01085.id !== id
      || fiveCopyGeometryReplayReflected01085.parents_replayed !== 1109220
      || fiveCopyGeometryReplayReflected01085.replay_failures !== 0
      || fiveCopyGeometryReplayReflected01085.canonical_sha256
        !== reflectedFiveCopy.five_copy_alcove_metatile_screen.canonical_sha256)) {
    throw new Error("Missing replayed reflected five-copy substitution exclusion for a2sp_9_01085");
  }
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  return {
    id,
    kind: "a2_sliced_palindromic_alcove_census",
    registry_id: `a2_sliced_pal_${id.slice("a2sp_".length)}`,
    name: `A2 Palindromic-Profile Size-9 ${isPeriodic ? "Periodic Control" : "Candidate"} ${id.slice("a2sp_9_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: index + 1,
    survivor_count: 97,
    description: isPeriodic
      ? "Nine-alcove non-polycube with a replayed eight-copy periodic quotient and induced scale-two cluster substitution."
      : `Nine-alcove non-polycube from the completed palindromic-profile stratum on consecutive x+y+z=k sections. A heavy-first ten-copy quotient campaign exactly excludes ${tenCopy.exact_negative_orbits} of ${tenCopy.orbit_total} proper-A₂ orbit classes, covering ${tenCopy.hnfs_exactly_excluded} of ${tenCopy.hnf_total} HNF bases.${tenCopyComplete ? " The fixed ten-copy determinant-15 screen is complete with zero solver unknowns." : ` The remaining ${tenCopy.node_capped_orbits} classes are explicitly inconclusive after ten-million-node searches.`} A separate radius-two core-CEGAR continuation retains ${radiusTwo.corona2_core_cegar.clauses.length} sound failure clauses after ${radiusTwo.corona2_core_cegar.rounds} rounds without exhausting the outer space or finding a replayed radius-two patch.${fiveCopies.length ? ` For this leader, the complete five-copy metatile alphabet${fiveCopies.length > 1 ? "s" : ""} at scale 2 ${fiveCopies.length > 1 ? "are" : "is"} also excluded across ${fiveCopies.reduce((sum, result) => sum + result.five_copy_alcove_metatile_screen.symmetry_distinct_metatiles, 0).toLocaleString("en-US")} connected parent/model cases, each with a replay-verified atomic local obstruction.` : ""} An alternate 120-second QF_FD probe on 18 residual classes yields no SAT or UNSAT result; 12 interrupted partial receipts are excluded.`,
    screening: {
      status: isPeriodic ? "periodic" : "inconclusive",
      certificate: isPeriodic ? "translational" : null,
      census_stage: isPeriodic
        ? "a2_sliced_size9_palindromic_eight_copy_positive_2026_08_30"
        : "a2_sliced_size9_complete_palindromic_profile_exact_through8_2026_08_30",
      complete_source_pool_size: 22607,
      recovered_source_pool_size: 1627,
      recovered_two_copy_periodic_certificates: 1135,
      recovered_four_copy_additional_periodic_certificates: 304,
      recovered_reflection_classes_through_four: 114,
      recovered_six_copy_additional_periodic_classes: 17,
      recovered_reflection_classes_through_six: 97,
      periodic_exact_through: tenCopyComplete ? 10 : 8,
      periodic_six_copy_hnf_total: sixCopy.periodic_z3.hnf_total,
      periodic_six_copy_hnf_covered: sixCopy.periodic_z3.hnf_covered,
      periodic_six_copy_solver_unknowns: 0,
      periodic_six_copy_exact_multicover_nodes: sixCopy.periodic_z3.exact_multicover_nodes,
      periodic_eight_copy_complete: !isPeriodic && record.periodic_z3.hnf_range_exhausted === true,
      periodic_eight_copy_orbit_representatives: record.periodic_z3.hnf_orbit_total,
      periodic_eight_copy_orbits_visited: record.periodic_z3.hnf_visited,
      periodic_eight_copy_hnf_covered: record.periodic_z3.hnf_covered,
      periodic_eight_copy_hnf_total: record.periodic_z3.hnf_total,
      periodic_eight_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_eight_copy_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_eight_copy_certificate: periodicCertificate,
      periodic_eight_copy_replay_verified: record.periodic_z3.replay?.verified ?? false,
      periodic_ten_copy_orbit_total: tenCopy?.orbit_total ?? 0,
      periodic_ten_copy_exact_negative_orbits: tenCopy?.exact_negative_orbits ?? 0,
      periodic_ten_copy_node_capped_orbits: tenCopy?.node_capped_orbits ?? 0,
      periodic_ten_copy_hnf_total: tenCopy?.hnf_total ?? 0,
      periodic_ten_copy_hnfs_exactly_excluded: tenCopy?.hnfs_exactly_excluded ?? 0,
      periodic_ten_copy_exact_multicover_nodes: tenCopy?.exact_multicover_nodes ?? 0,
      periodic_ten_copy_milliseconds: tenCopy?.milliseconds ?? 0,
      periodic_ten_copy_exact_node_limits: tenCopy
        ? tenCopySummary.exact_node_limits_per_orbit : [],
      periodic_ten_copy_complete: tenCopyComplete,
      periodic_ten_copy_qffd_timeout_ms: tenCopy ? tenCopySolverProbe.timeout_ms_per_orbit : 0,
      periodic_ten_copy_qffd_completed_shards: tenCopy ? tenCopySolverProbe.completed_shards : 0,
      periodic_ten_copy_qffd_solver_unknown_shards: tenCopy ? tenCopySolverProbe.solver_unknown_shards : 0,
      periodic_ten_copy_qffd_partial_receipts_excluded: tenCopy
        ? tenCopySolverProbe.partial_interrupted_receipts_excluded : 0,
      periodic_ten_copy_summary_report: tenCopy
        ? "data/a2-sliced-size9-palindromic-periodic10-exact10m-summary.json" : null,
      periodic_ten_copy_receipt_archive: tenCopy
        ? "data/a2-sliced-size9-palindromic-periodic10-best10m-receipts.ndjson.gz" : null,
      radius_two_status: radiusTwo?.corona2_core_classification ?? null,
      radius_two_rounds: radiusTwo?.corona2_core_cegar?.rounds ?? 0,
      radius_two_failure_clauses: radiusTwo?.corona2_core_cegar?.clauses?.length ?? 0,
      radius_two_outer_exhausted: radiusTwo?.corona2_core_cegar?.outer_exhausted ?? false,
      radius_two_stopped_by: radiusTwo?.corona2_core_cegar?.stopped_by ?? null,
      radius_two_cumulative_milliseconds:
        radiusTwo?.corona2_core_cegar?.cumulative_milliseconds ?? 0,
      radius_two_report: radiusTwo
        ? "data/a2-sliced-size9-palindromic-corona2-core256.ndjson.gz" : null,
      motif_tiles: periodicCertificate?.copies ?? null,
      period_vectors: periodicCertificate?.period_vectors ?? null,
      quotient_determinant: periodicCertificate?.determinant ?? null,
      periodic_template: webPeriodicTemplate(periodicCertificate, makeA2SlicedAlcoveUnion(record.alcoves)),
      periodic_source: isPeriodic
        ? "an exact eight-copy weighted quotient, independently replayed together with its induced scale-two cluster substitution"
        : null,
      periodic_quotient_cluster_substitution: clusterSubstitution?.substitution ?? null,
      periodic_quotient_cluster_substitution_report: clusterSubstitution
        ? "data/a2-sliced-size9-palindromic-periodic-cluster-substitutions.ndjson.gz" : null,
      direct_scalar_substitution_exact_scales: [2, 8],
      direct_scalar_substitution_models: ["proper", "reflected"],
      direct_scalar_substitution_certified_negatives: direct.length,
      direct_scalar_substitution_report: "data/a2-sliced-size9-palindromic-direct-substitution-scale2to8.ndjson.gz",
      two_copy_substitution_exact_scales: [2, 3],
      two_copy_substitution_models: ["proper", "reflected"],
      two_copy_substitution_certified_negatives: twoCopy.length,
      two_copy_substitution_parents_exhausted: twoCopy.reduce((sum, result) =>
        sum + result.two_copy_alcove_metatile_screen.parents_completed, 0),
      two_copy_substitution_report: "data/a2-sliced-size9-palindromic-two-copy-substitution-scale2to3.ndjson.gz",
      three_copy_substitution_exact_scales: [...new Set(threeCopy.map(result =>
        result.three_copy_alcove_metatile_screen.scale))].sort((left, right) => left - right),
      three_copy_substitution_models: ["proper", "reflected"],
      three_copy_substitution_certified_negatives: threeCopy.length,
      three_copy_substitution_parents_exhausted: threeCopy.reduce((sum, result) =>
        sum + result.three_copy_alcove_metatile_screen.parents_completed, 0),
      three_copy_substitution_report: "data/a2-sliced-size9-palindromic-three-copy-substitution-scale2.ndjson.gz",
      three_copy_substitution_reports: [
        "data/a2-sliced-size9-palindromic-three-copy-substitution-scale2.ndjson.gz",
        ...(id === "a2sp_9_04636"
          ? ["data/a2-sliced-size9-palindromic-three-copy-substitution-scale3-04636.ndjson.gz"]
          : ["a2sp_9_01085", "a2sp_9_04468"].includes(id)
            ? ["data/a2-sliced-size9-palindromic-three-copy-substitution-scale3-additional-leaders.ndjson.gz"]
            : [])
      ],
      four_copy_substitution_exact_scales: fourCopy.length ? [2] : [],
      four_copy_substitution_models: fourCopy.length ? ["proper", "reflected"] : [],
      four_copy_substitution_certified_negatives: fourCopy.length,
      four_copy_substitution_parents_exhausted: fourCopy.reduce((sum, result) =>
        sum + result.four_copy_alcove_metatile_screen.parents_completed, 0),
      four_copy_substitution_reports: fourCopy.length ? [
        "data/a2-sliced-size9-palindromic-four-copy-substitution-scale2-proper-leaders.ndjson.gz",
        "data/a2-sliced-size9-palindromic-four-copy-substitution-scale2-reflected-leaders.ndjson.gz"
      ] : [],
      five_copy_substitution_exact_scales: fiveCopy ? [2] : [],
      five_copy_substitution_models: [
        ...(fiveCopy ? ["proper"] : []),
        ...(reflectedFiveCopy ? ["reflected"] : [])
      ],
      five_copy_substitution_certified_negatives: fiveCopies.length,
      five_copy_substitution_parents_exhausted: fiveCopies.reduce((sum, result) =>
        sum + result.five_copy_alcove_metatile_screen.parents_completed, 0),
      five_copy_substitution_report: fiveCopy
        ? `data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-${id.slice("a2sp_9_".length)}.ndjson.gz`
        : null,
      five_copy_substitution_summary_report: id === "a2sp_9_04468"
        ? "data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-04468-summary.json"
        : null,
      five_copy_substitution_reports: fiveCopies.map(result =>
        `data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-${result.five_copy_alcove_metatile_screen.include_reflections ? "reflected" : "proper"}-${id.slice("a2sp_9_".length)}.ndjson.gz`
      ),
      five_copy_substitution_summary_reports: [
        ...(id === "a2sp_9_04468"
          ? ["data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-proper-04468-summary.json"]
          : []),
        ...(reflectedFiveCopy
          ? [`data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-${id.slice("a2sp_9_".length)}-summary.json`]
          : [])
      ],
      five_copy_substitution_geometric_replay_reports: reflectedFiveCopy
        ? [`data/a2-sliced-size9-palindromic-five-copy-substitution-scale2-reflected-${id.slice("a2sp_9_".length)}-geometric-replay.json`]
        : [],
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_solver: corona.corona_z3.smt2_sha256 ? "z3" : "exact_gcts",
      corona_report: corona.corona_z3.smt2_sha256
        ? `data/a2-sliced-size9-palindromic-corona-z3-${id.slice("a2sp_9_".length)}.ndjson.gz`
        : "data/a2-sliced-size9-palindromic-focused-corona1-bounded.ndjson.gz",
      periodic_report: "data/a2-sliced-size9-palindromic-periodic-exact8-complete.ndjson.gz"
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
