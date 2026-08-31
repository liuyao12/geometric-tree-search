#!/usr/bin/env node
/** Build the leading exact-through-six candidates from the complete size-ten census. */

import { readFile, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { makeA2SlicedAlcoveUnion } from "../assets/a2-sliced-alcoves.js";

const root = new URL("../", import.meta.url);
const readGzipNdjson = async relativePath => gunzipSync(
  await readFile(new URL(relativePath, root))
).toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
const readJson = async relativePath => JSON.parse(await readFile(new URL(relativePath, root), "utf8"));

const sixCopyRows = await readGzipNdjson(
  "data/a2-sliced-size10-focused-periodic-exact6-ranks9-72.ndjson.gz"
);
const coronaRows = await readGzipNdjson(
  "data/a2-sliced-size10-focused-corona1-bounded.ndjson.gz"
);
const directSubstitutions = await readGzipNdjson(
  "data/a2-sliced-size10-direct-substitution-scale2to8.ndjson.gz"
);
const twoCopySubstitutions = await readGzipNdjson(
  "data/a2-sliced-size10-two-copy-substitution-scale2to3.ndjson.gz"
);
const threeCopySubstitutions = await readGzipNdjson(
  "data/a2-sliced-size10-three-copy-substitution-scale2-leaders.ndjson.gz"
);
const fourCopySubstitutions = await readGzipNdjson(
  "data/a2-sliced-size10-four-copy-substitution-scale2-proper-leaders.ndjson.gz"
);
const nineCopySummary = await readJson(
  "data/a2-sliced-size10-leaders-periodic9-exact2m-summary.json"
);
const nineCopyCertificates = await readGzipNdjson(
  "data/a2-sliced-size10-36194-periodic9-certificate.ndjson.gz"
);
const nineCopyClusterRules = await readGzipNdjson(
  "data/a2-sliced-size10-36194-periodic9-cluster-substitution.ndjson.gz"
);
const sixCopyById = new Map(sixCopyRows.map(record => [record.id, record]));
const coronaById = new Map(coronaRows.map(record => [record.id, record]));
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
const selectedIds = ["a2sa_10_36141", "a2sa_10_35323", "a2sa_10_36194"];
const nineCopySummaryById = new Map(nineCopySummary.candidates.map(record => [record.id, record]));
const nineCopyCertificateById = new Map(nineCopyCertificates.map(record => [record.id, record]));
const nineCopyClusterById = new Map(nineCopyClusterRules.map(record => [record.id, record]));
const fourCopySubstitutionById = new Map(fourCopySubstitutions.map(record => [record.id, record]));

const proofOrientationTransforms = [
  [1, [0, 1, 2]], [1, [1, 2, 0]], [1, [2, 0, 1]],
  [-1, [0, 2, 1]], [-1, [1, 0, 2]], [-1, [2, 1, 0]]
];
const webPeriodicTemplate = (certificate, geometry) => {
  if (!certificate) return null;
  const shifts = proofOrientationTransforms.map(([sign, permutation]) =>
    [0, 1, 2].map(axis => Math.min(...geometry.v.map(vertex => sign * vertex[permutation[axis]])))
  );
  const hashes = proofOrientationTransforms.map(([sign, permutation], index) => {
    const transform = point => [0, 1, 2].map(axis => sign * point[permutation[axis]] - shifts[index][axis]);
    return `${geometry.v.map(transform).map(p => p.join(",")).sort().join("|")}@@${geometry.occ.map(([p, w]) => `${transform(p).join(",")}:${w}`).sort().join("|")}`;
  });
  const webHashes = [];
  for (const proofIndex of [0, 3, 4, 1, 2, 5]) if (!webHashes.includes(hashes[proofIndex])) webHashes.push(hashes[proofIndex]);
  const proofToWeb = hashes.map(hash => webHashes.indexOf(hash));
  const rootShift = shifts[certificate.placements[0].orientation_index].map(value => -value);
  return {
    period_vectors: certificate.period_vectors,
    motif: certificate.placements.map(placement => ({
      prototile_idx: 0,
      orientation_index: proofToWeb[placement.orientation_index],
      translation: placement.translation.map((value, axis) => value + shifts[placement.orientation_index][axis] + rootShift[axis])
    }))
  };
};

const candidates = selectedIds.map((id, index) => {
  const record = sixCopyById.get(id);
  const corona = coronaById.get(id);
  const direct = directSubstitutionById.get(id) ?? [];
  const twoCopy = twoCopySubstitutionById.get(id) ?? [];
  const threeCopy = threeCopySubstitutionById.get(id) ?? [];
  const fourCopy = fourCopySubstitutionById.get(id) ?? null;
  const nineCopy = nineCopySummaryById.get(id);
  const nineCopyRecord = nineCopyCertificateById.get(id);
  const periodicCertificate = nineCopyRecord?.periodic_z3?.certificate ?? null;
  const clusterRule = nineCopyClusterById.get(id)?.substitution ?? null;
  const isPeriodic = periodicCertificate !== null;
  if (!record || record.classification !== "unresolved"
      || record.periodic_z3.hnf_range_exhausted !== true
      || record.periodic_z3.solver_unknown !== 0
      || record.periodic_z3.hnf_covered !== 217) {
    throw new Error(`Missing complete six-copy exclusion for ${id}`);
  }
  if (!corona || corona.corona_classification !== "root_corona_exists"
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
  if (threeCopy.length !== 2 || threeCopy.some(result =>
    !result.classification.startsWith("no_three_copy_metatile_scalar")
    || result.three_copy_alcove_metatile_screen.certified !== true)) {
    throw new Error(`Missing scale-2 three-copy substitution exclusions for ${id}`);
  }
  if (!isPeriodic && (!fourCopy
      || fourCopy.classification !== "no_four_copy_metatile_scalar2_substitution"
      || fourCopy.four_copy_alcove_metatile_screen.certified !== true)) {
    throw new Error(`Missing proper scale-2 four-copy substitution exclusion for ${id}`);
  }
  const geometry = makeA2SlicedAlcoveUnion(record.alcoves);
  return {
    id,
    kind: "a2_sliced_size10_alcove_census",
    registry_id: `a2_sliced_${id.slice("a2sa_".length)}`,
    name: `A2 Consecutive-Layer Size-10 ${isPeriodic ? "Periodic Control" : "Candidate"} ${id.slice("a2sa_10_".length)}`,
    alcoves: record.alcoves,
    morphology: record.morphology,
    lattice_points: geometry.occ.length,
    survivor_priority: index + 1,
    survivor_count: 13,
    description: "Ten-alcove non-polycube from the complete consecutive-section census on x+y+z=k.",
    screening: {
      status: isPeriodic ? "periodic" : "inconclusive",
      certificate: isPeriodic ? "translational" : null,
      census_stage: isPeriodic ? "a2_sliced_size10_nine_copy_positive_2026_08_31" : "a2_sliced_size10_nine_copy_bounded_2026_08_31",
      source_pool_size: 98537,
      three_copy_periodic_certificates: 2558,
      three_copy_proper_survivors: 95979,
      three_copy_reflection_classes: 48209,
      focused_six_copy_classes: 72,
      focused_six_copy_periodic_certificates: 59,
      focused_six_copy_survivors: 13,
      periodic_six_copy_hnf_total: record.periodic_z3.hnf_total,
      periodic_six_copy_hnf_covered: record.periodic_z3.hnf_covered,
      periodic_six_copy_orbit_representatives: record.periodic_z3.hnf_orbit_total,
      periodic_six_copy_solver_unknowns: record.periodic_z3.solver_unknown,
      periodic_six_copy_exact_multicover_nodes: record.periodic_z3.exact_multicover_nodes,
      periodic_six_copy_milliseconds: record.periodic_z3.milliseconds,
      periodic_exact_through: isPeriodic ? 9 : 6,
      periodic_nine_copy_orbit_total: nineCopy.orbit_total,
      periodic_nine_copy_exact_negative_orbits: nineCopy.exact_negative_orbits,
      periodic_nine_copy_node_capped_orbits: nineCopy.node_capped_orbits,
      periodic_nine_copy_hnfs_exactly_excluded: nineCopy.hnfs_exactly_excluded,
      periodic_nine_copy_exact_multicover_nodes: nineCopy.exact_multicover_nodes,
      periodic_nine_copy_certificate: periodicCertificate,
      periodic_nine_copy_replay_verified: nineCopyRecord?.periodic_z3?.replay?.verified ?? false,
      motif_tiles: periodicCertificate?.copies ?? null,
      period_vectors: periodicCertificate?.period_vectors ?? null,
      quotient_determinant: periodicCertificate?.determinant ?? null,
      periodic_template: webPeriodicTemplate(periodicCertificate, geometry),
      periodic_source: isPeriodic ? "an exact nine-copy weighted quotient with an independently replayed scale-two cluster substitution" : null,
      periodic_quotient_cluster_substitution: clusterRule,
      periodic_report: "data/a2-sliced-size10-leaders-periodic9-exact2m-summary.json",
      direct_scalar_substitution_exact_scales: [2, 8],
      direct_scalar_substitution_models: ["proper", "reflected"],
      direct_scalar_substitution_certified_negatives: direct.length,
      direct_scalar_substitution_report: "data/a2-sliced-size10-direct-substitution-scale2to8.ndjson.gz",
      two_copy_substitution_exact_scales: [2, 3],
      two_copy_substitution_models: ["proper", "reflected"],
      two_copy_substitution_certified_negatives: twoCopy.length,
      two_copy_substitution_parents_exhausted: twoCopy.reduce((sum, result) =>
        sum + result.two_copy_alcove_metatile_screen.parents_completed, 0),
      two_copy_substitution_report: "data/a2-sliced-size10-two-copy-substitution-scale2to3.ndjson.gz",
      three_copy_substitution_exact_scales: [2],
      three_copy_substitution_models: ["proper", "reflected"],
      three_copy_substitution_certified_negatives: threeCopy.length,
      three_copy_substitution_parents_exhausted: threeCopy.reduce((sum, result) =>
        sum + result.three_copy_alcove_metatile_screen.parents_completed, 0),
      three_copy_substitution_report: "data/a2-sliced-size10-three-copy-substitution-scale2-leaders.ndjson.gz",
      four_copy_substitution_exact_scales: fourCopy ? [2] : [],
      four_copy_substitution_models: fourCopy ? ["proper"] : [],
      four_copy_substitution_certified_negatives: fourCopy ? 1 : 0,
      four_copy_substitution_parents_exhausted:
        fourCopy?.four_copy_alcove_metatile_screen.parents_completed ?? 0,
      four_copy_substitution_report: fourCopy
        ? "data/a2-sliced-size10-four-copy-substitution-scale2-proper-leaders.ndjson.gz" : null,
      corona_root_patch_copies: corona.corona_z3.replay.patch_copies,
      corona_search_nodes: corona.corona_z3.exact_gcts.nodes,
      corona_report: "data/a2-sliced-size10-focused-corona1-bounded.ndjson.gz",
      deeper_periodic_domains_open: true
    },
    root_corona_witness: corona.corona_z3.witness
  };
});

await writeFile(
  new URL("assets/a2-sliced-size10-candidates.js", root),
  `// Generated by scripts/build-a2-sliced-size10-catalog.mjs.\n`
    + `export const A2_SLICED_SIZE10_CANDIDATES = Object.freeze(${JSON.stringify(candidates, null, 2)});\n`,
  "utf8"
);
console.log(JSON.stringify({ candidates: selectedIds }, null, 2));
