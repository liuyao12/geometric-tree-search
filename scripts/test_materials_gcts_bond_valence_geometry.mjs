import assert from "node:assert/strict";
import { bondValenceParameter, bondValenceSums, bondValenceStateSummary,
  incrementalBondValenceSatisfaction,
  BOND_VALENCE_PROVENANCE } from "../apps/iqc-growth-live/bond-valence-geometry.js";

const site = (species, charge, position) => ({ species, charge, position });

const na = site("Na", 1, [0, 0, 0]);
const chlorideShell = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
  .map(([x, y, z]) => site("Cl", -1, [2.82 * x, 2.82 * y, 2.82 * z]));
const nacl = bondValenceSums([na, ...chlorideShell]);
assert.equal(nacl.available, true);
assert.equal(nacl.pairCount, 6);
assert.ok(Math.abs(nacl.sites[0].sum - .9801) < .01);
assert.equal(nacl.usedParameters[0].r0, 2.15);
assert.equal(nacl.usedParameters[0].b, .37);
assert.ok(nacl.sites[0].vectorMagnitude < 1e-12);
assert.ok(nacl.meanVectorMagnitude > 0);

const neighborhoods = [[na, ...chlorideShell],
  ...chlorideShell.map((chloride) => [chloride, na])];
const state = bondValenceStateSummary(neighborhoods);
assert.equal(state.available, true);
assert.equal(state.suppliedCenters, 7);
assert.equal(state.resolvedCenters, 7);
assert.ok(Number.isFinite(state.sampledRmsValenceMismatch));
assert.ok(Number.isFinite(state.sampledMeanVectorMagnitude));
assert.ok(state.centerRecords[0].vectorMagnitude < 1e-12);
const transform = ([x, y, z]) => [-y + 8, x - 3, z + 4];
const transformedState = bondValenceStateSummary(neighborhoods.map((neighborhood) =>
  neighborhood.map((record) => ({ ...record, position: transform(record.position) }))));
assert.ok(Math.abs(transformedState.sampledRmsValenceMismatch
  - state.sampledRmsValenceMismatch) < 1e-12);
assert.ok(Math.abs(transformedState.sampledMeanVectorMagnitude
  - state.sampledMeanVectorMagnitude) < 1e-12);

const incremental = incrementalBondValenceSatisfaction(chlorideShell, [na]);
assert.equal(incremental.available, true);
assert.ok(incremental.score > 0);
assert.ok(incremental.vectorScore > 0);
assert.ok(incremental.combinedScore > 0);
assert.ok(incremental.afterVectorBurden < incremental.beforeVectorBurden);
assert.equal(incremental.resolvedAddedSites, 1);
assert.equal(incremental.addedBondCount, 6);
assert.equal(incremental.uniformScaleInvariant, false);
assert.equal(incremental.targetUsed, false);
assert.equal(incremental.candidateGeometryChanged, false);
assert.equal(incremental.hardAdmissionChanged, false);

const translated = incrementalBondValenceSatisfaction(
  chlorideShell.map((record) => ({ ...record, position: record.position.map((value, axis) => value + [8, -3, 4][axis]) })),
  [{ ...na, position: [8, -3, 4] }]);
assert.ok(Math.abs(translated.score - incremental.score) < 1e-12);
assert.ok(Math.abs(translated.vectorScore - incremental.vectorScore) < 1e-12);

const rotated = incrementalBondValenceSatisfaction(
  chlorideShell.map((record) => ({ ...record, position: [-record.position[1], record.position[0], record.position[2]] })), [na]);
assert.ok(Math.abs(rotated.score - incremental.score) < 1e-12);
assert.ok(Math.abs(rotated.vectorScore - incremental.vectorScore) < 1e-12);

const asymmetric = incrementalBondValenceSatisfaction(chlorideShell.slice(0, 3), [na]);
assert.equal(asymmetric.available, true);
assert.ok(asymmetric.vectorScore < incremental.vectorScore);

const scaled = incrementalBondValenceSatisfaction(
  chlorideShell.map((record) => ({ ...record, position: record.position.map((value) => 1.1 * value) })), [na]);
assert.notEqual(scaled.score, incremental.score);

assert.equal(bondValenceParameter(site("H", 1, [0, 0, 0]), site("O", -2, [.96, 0, 0]), .96).r0, .907);
assert.equal(bondValenceParameter(site("H", 1, [0, 0, 0]), site("O", -2, [1.3, 0, 0]), 1.3).r0, .569);
assert.equal(bondValenceParameter(site("H", 1, [0, 0, 0]), site("O", -2, [1.9, 0, 0]), 1.9).r0, .990);

const unsupported = incrementalBondValenceSatisfaction(
  [site("Cd", 2, [0, 0, 0])], [site("Yb", -2, [2.8, 0, 0])]);
assert.equal(unsupported.available, false);
assert.match(unsupported.reason, /no checked bond-valence parameter/);
const unsupportedState = bondValenceStateSummary([
  [site("Cd", 2, [0, 0, 0]), site("Yb", -2, [2.8, 0, 0])],
]);
assert.equal(unsupportedState.available, false);
assert.equal(BOND_VALENCE_PROVENANCE.revision, "2020-11-25");
assert.equal(BOND_VALENCE_PROVENANCE.vectorRuleDoi, "10.1107/S0108768106026553");
assert.match(BOND_VALENCE_PROVENANCE.vectorRuleCaveat, /anisotropy/);

console.log("bond-valence geometry tests passed");
