import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import {
  a2SlicedAlcoveNeighbors,
  a2SlicedAlcoveVertices,
  canonicalA2SlicedAlcoves,
  enumerateA2SlicedAlcoves,
  makeA2SlicedAlcoveUnion
} from "../assets/a2-sliced-alcoves.js";
import { preprocessTilingSystem, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const seed = { base: [0, 0, 0], order: [0, 1, 2] };
assert.deepEqual(a2SlicedAlcoveVertices(seed).map(point => point.reduce((a, b) => a + b, 0)), [0, 1, 2, 3]);
assert.equal(a2SlicedAlcoveNeighbors(seed).length, 4);
for (const neighbor of a2SlicedAlcoveNeighbors(seed)) {
  const common = new Set(a2SlicedAlcoveVertices(seed).map(String));
  assert.equal(a2SlicedAlcoveVertices(neighbor).filter(point => common.has(String(point))).length, 3);
}

const shifted = { base: [7, -3, 11], order: [0, 1, 2] };
assert.equal(canonicalA2SlicedAlcoves([seed]).key, canonicalA2SlicedAlcoves([shifted]).key);

const expected = [1, 2, 7, 22, 83, 314];
for (let size = 1; size <= expected.length; size += 1) {
  const census = enumerateA2SlicedAlcoves({ size });
  assert.equal(census.length, expected[size - 1], `size-${size} alcove census`);
  assert.ok(census.every(candidate => candidate.morphology.layer_equation === "x+y+z=k"));
}

const single = makeA2SlicedAlcoveUnion([seed]);
assert.deepEqual(single.occ.map(entry => entry[1]).sort((a, b) => a - b), [1, 1, 3, 3]);
assert.deepEqual(single.layer_sums, [0, 1, 2, 3]);
assert.equal(single.geometry_model, "lattice_function");
assert.equal(single.lattice_symmetry, "a2_layers");
const pair = makeA2SlicedAlcoveUnion([seed, a2SlicedAlcoveNeighbors(seed)[2]]);
assert.equal(pair.f_data.length, 6, "the shared triangular face must be removed");
assert.ok(pair.occ.every(entry => Number.isInteger(entry[1]) && entry[1] > 0 && entry[1] <= 48));

const prepared = preprocessTilingSystem({
  mode_key: "cube",
  include_mirrors: false,
  custom_system: {
    name: "A2-sliced probe",
    a2_sliced_alcoves: [{ name: "alcove pair", alcoves: [seed, a2SlicedAlcoveNeighbors(seed)[2]] }]
  }
}, tileSpecs);
assert.equal(prepared.summary.point_group_order, 6);
assert.equal(prepared.prototiles[0].geometry_model, "lattice_function");
assert.equal(prepared.prototiles[0].is_polycube, false);
assert.ok(prepared.prototiles[0].unique_orientations.length > 1);

const readNdjson = async path => (await readFile(new URL(path, import.meta.url), "utf8"))
  .trim().split("\n").filter(Boolean).map(JSON.parse);
const readGzipNdjson = async path => gunzipSync(await readFile(new URL(path, import.meta.url)))
  .toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
const sizeSix = await readNdjson("../data/a2-sliced-alcove-size6-directed-periodic-exact1.ndjson");
assert.equal(sizeSix.length, 222);
assert.ok(sizeSix.every(record =>
  record.classification === "periodic"
  && record.periodic_z3.certificate.certified
  && record.periodic_z3.certificate.copies === 1
  && record.periodic_z3.certificate.determinant === 1
  && record.periodic_z3.replay.verified
));
const sizeSeven = await readNdjson("../data/a2-sliced-alcove-size7-directed-periodic-exact6.ndjson");
assert.equal(sizeSeven.length, 1112);
assert.equal(sizeSeven.filter(record => record.classification === "periodic").length, 853);
assert.equal(sizeSeven.filter(record => record.classification === "unresolved").length, 259);
assert.ok(sizeSeven.filter(record => record.classification === "periodic").every(record =>
  record.periodic_z3.certificate.copies === 6
  && record.periodic_z3.certificate.determinant === 7
  && record.periodic_z3.replay.verified
));
assert.ok(sizeSeven.filter(record => record.classification === "unresolved").every(record =>
  record.periodic_z3.solver_unknown === 0
  && record.periodic_z3.hnf_covered === 57
  && record.periodic_z3.exhausted_by_copies[6] === 57
));
assert.equal(sizeSeven.reduce((sum, record) =>
  sum + record.periodic_z3.exact_multicover_nodes, 0), 206993651);

const coronas = await readNdjson("../data/a2-sliced-alcove-size7-directed-corona1.ndjson");
assert.equal(coronas.length, 259);
assert.equal(coronas.filter(record => record.corona_classification === "root_corona_exists").length, 259);
assert.ok(coronas.filter(record => record.corona_classification === "root_corona_exists")
  .every(record => record.corona_z3.replay.verified));

const sizeEightThree = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-directed-periodic-exact3.ndjson.gz"
);
assert.equal(sizeEightThree.length, 4406);
assert.equal(sizeEightThree.filter(record => record.classification === "periodic").length, 3335);
assert.equal(sizeEightThree.filter(record => record.classification === "unresolved").length, 1071);
assert.ok(sizeEightThree.filter(record => record.classification === "periodic").every(record =>
  record.periodic_z3.certificate.copies === 3
  && record.periodic_z3.certificate.determinant === 4
  && record.periodic_z3.replay.verified
));
assert.ok(sizeEightThree.filter(record => record.classification === "unresolved").every(record =>
  record.periodic_z3.solver_unknown === 0
  && record.periodic_z3.hnf_range_exhausted
));

const sizeEight = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-directed-periodic-exact6.ndjson.gz"
);
assert.equal(sizeEight.length, 4406);
assert.equal(sizeEight.filter(record => record.classification === "periodic").length, 4380);
assert.equal(sizeEight.filter(record => record.classification === "unresolved").length, 26);
assert.ok(sizeEight.filter(record => record.classification === "periodic").every(record =>
  record.periodic_z3.certificate.copies === 6
  && record.periodic_z3.certificate.determinant === 8
  && record.periodic_z3.replay.verified
));
assert.ok(sizeEight.filter(record => record.classification === "unresolved").every(record =>
  record.periodic_z3.solver_unknown === 0
  && record.periodic_z3.hnf_range_exhausted
));
const sizeEightThreeById = new Map(sizeEightThree.map(record => [record.id, record]));
assert.ok(sizeEight.filter(record => record.classification === "unresolved").every(record =>
  sizeEightThreeById.get(record.id)?.classification === "unresolved"
));
assert.equal(sizeEight.filter(record =>
  sizeEightThreeById.get(record.id)?.classification === "unresolved"
  && record.classification === "periodic").length, 1045);
const sizeEightRepresentatives = await readNdjson(
  "../data/a2-sliced-alcove-size8-directed-exact6-reflection-representatives.ndjson"
);
assert.equal(sizeEightRepresentatives.length, 15);
assert.deepEqual(sizeEightRepresentatives.map(record => record.survivor_priority),
  Array.from({ length: 15 }, (_, index) => index + 1));
assert.ok(sizeEightRepresentatives.every(record => record.reflection_class.members.includes(record.id)));
const sizeEightTwelveCopyPositive = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-directed-periodic-exact12-positive.ndjson.gz"
);
assert.equal(sizeEightTwelveCopyPositive.length, 7);
assert.ok(sizeEightTwelveCopyPositive.every(record =>
  record.classification === "periodic"
  && record.periodic_z3.certificate.copies === 12
  && record.periodic_z3.certificate.determinant === 16
  && record.periodic_z3.replay.verified
));
const sizeEightFourCopyProper = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-four-cluster-scale2-proper.ndjson.gz"
);
assert.equal(sizeEightFourCopyProper.length, 13);
assert.ok(sizeEightFourCopyProper.every(record =>
  record.classification === "no_four_copy_metatile_scalar2_substitution"
  && record.four_copy_alcove_metatile_screen.certified
  && record.four_copy_alcove_metatile_screen.scale === 2
  && record.four_copy_alcove_metatile_screen.include_reflections === false
));
assert.deepEqual(new Set(sizeEightFourCopyProper.map(record => record.id)),
  new Set(sizeEightRepresentatives.map(record => record.id).filter(id =>
    !["a2sa_8_00888", "a2sa_8_02965"].includes(id))));
const sizeEightAnisotropic = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-anisotropic-cellularity-through8.ndjson.gz"
);
assert.equal(sizeEightAnisotropic.length, 130);
assert.ok(sizeEightAnisotropic.every(record =>
  record.anisotropic_substitution_classification === "inflation_not_alcove_cellular"
  && record.anisotropic_substitution.certified
  && record.anisotropic_substitution.claim_scope
    === "fixed_affine_A3_alcove_cellular_substitution_only"
  && record.anisotropic_substitution.noncellular_substitution_open
));
assert.ok([...new Set(sizeEightAnisotropic.map(record =>
  `${record.anisotropic_substitution.planar_scale},${record.anisotropic_substitution.layer_scale}`
))].length === 10);
const sizeEightFourCopyReflected = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-four-cluster-scale2-reflected-summary.ndjson.gz"
);
assert.equal(sizeEightFourCopyReflected.length, 13);
assert.deepEqual(new Set(sizeEightFourCopyReflected.map(record => record.id)),
  new Set(sizeEightRepresentatives.map(record => record.id).filter(id =>
    !["a2sa_8_00888", "a2sa_8_02965"].includes(id))));
assert.ok(sizeEightFourCopyReflected.every(record =>
  record.classification === "no_four_copy_metatile_scalar2_substitution"
  && record.four_copy_alcove_metatile_screen.certified
  && record.four_copy_alcove_metatile_screen.parents_completed
    === record.four_copy_alcove_metatile_screen.symmetry_distinct_metatiles
));
assert.equal(Math.min(...sizeEightFourCopyReflected.map(record =>
  record.four_copy_alcove_metatile_screen.symmetry_distinct_metatiles)), 108503);
assert.equal(Math.max(...sizeEightFourCopyReflected.map(record =>
  record.four_copy_alcove_metatile_screen.symmetry_distinct_metatiles)), 294950);
const sizeEightCoronas = await readNdjson(
  "../data/a2-sliced-alcove-size8-directed-corona1.ndjson"
);
assert.equal(sizeEightCoronas.length, 15);
assert.ok(sizeEightCoronas.every(record =>
  record.corona_classification === "root_corona_exists"
  && record.corona_z3.replay.verified
));
const sizeEightExtensions = await readNdjson(
  "../data/a2-sliced-alcove-size8-directed-retained-corona-extension.ndjson"
);
assert.equal(sizeEightExtensions.filter(record =>
  record.retained_corona_extension_classification === "radius2_witness").length, 1);
const sizeEightCorona2 = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-directed-corona2-gcts.ndjson.gz"
);
assert.equal(sizeEightCorona2.length, 14);
assert.equal(sizeEightCorona2.filter(record =>
  record.corona2_core_classification === "radius2_witness").length, 6);
assert.ok(sizeEightCorona2.filter(record =>
  record.corona2_core_classification === "radius2_witness").every(record =>
    record.corona2_core_cegar.replay.verified));
assert.equal(sizeEightCorona2.reduce((sum, record) =>
  sum + (record.corona2_core_cegar.clauses?.length ?? 0), 0), 4991);
const sizeEightRadius3 = await readGzipNdjson(
  "../data/a2-sliced-alcove-size8-directed-radius3-gcts.ndjson.gz"
);
assert.equal(sizeEightRadius3.length, 6);
assert.ok(sizeEightRadius3.every(record =>
  record.radius3_gcts_classification === "unresolved"
  && record.radius3_gcts.outer_exhausted === false
  && record.radius3_gcts.stopped_by
));
assert.equal(sizeEightRadius3.reduce((sum, record) =>
  sum + record.radius3_gcts.first_corona_failure_clauses.length, 0), 318);

console.log("A2-sliced alcove census regression passed", {
  expected,
  size_eight_three_copy_periodic: 3335,
  size_eight_periodic: 4380,
  size_eight_twelve_copy_periodic: 7,
  size_eight_current_survivors: 8,
  size_eight_reflection_classes: 15,
  size_eight_radius2_witnesses: 7
});
