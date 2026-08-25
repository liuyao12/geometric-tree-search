import assert from "node:assert/strict";
import { canonicalElement, makeLearningSupercell, nomadArchiveToStructure, normalizeElements, queryPayload, randomNomadStructure } from "../apps/iqc-growth-live/structure-database.js";

assert.equal(canonicalElement("na"), "Na");
assert.throws(() => canonicalElement("Xx"), /Unknown element/);
assert.throws(() => canonicalElement(""), /Unknown element/);

assert.deepEqual(normalizeElements(["al", "Cu", "Fe", "Cu"]), ["Al", "Cu", "Fe"]);
assert.throws(() => normalizeElements([]), /at least one/);
const payload = queryPayload(["Al", "Cu", "Fe"], 17);
assert.deepEqual(payload.query.and[0]["results.material.elements"].all, ["Al", "Cu", "Fe"]);
assert.equal(payload.query.and[1]["results.material.n_elements"], 3);
assert.equal(payload.query.and[2]["results.material.structural_type"], "bulk");
assert.equal(payload.pagination.page_offset, 17);

const entry = {
  entry_id: "test-entry",
  results: { material: {
    material_id: "test-material", elements: ["Cl", "Na"], chemical_formula_reduced: "ClNa",
    symmetry: { crystal_system: "cubic", space_group_number: 225, space_group_symbol: "Fm-3m" },
  } },
};
const archive = { data: { archive: { run: [{ program: { name: "VASP", version: "test-version" }, system: [{ atoms: {
  labels: ["Na", "Cl"],
  positions: [[0, 0, 0], [2.82e-10, 0, 0]],
  lattice_vectors: [[5.64e-10, 0, 0], [0, 5.64e-10, 0], [0, 0, 5.64e-10]],
  periodic: [true, true, true],
} }], calculation: [{ system_ref: "/run/0/system/0", method_ref: "/run/0/method/0",
  energy: { total: { value: -3.204353268e-18 } },
  forces: { total: { value: [[0, 1.602176634e-9, 0], [0, 0, -3.204353268e-9]] } },
}] }] } } };
const primitive = nomadArchiveToStructure(entry, archive);
assert.ok(Math.abs(primitive.atoms[1].position[0] - 2.82) < 1e-12);
assert.equal(primitive.metadata.spaceGroupNumber, 225);
assert.equal(primitive.metadata.materialId, "test-material");
assert.equal(primitive.metadata.calculation.programName, "VASP");
assert.equal(primitive.metadata.calculation.systemReference, "/run/0/system/0");
assert.ok(Math.abs(primitive.metadata.calculation.totalEnergyElectronVolt + 20) < 1e-12);
assert.ok(Math.abs(primitive.metadata.calculation.energyPerPrimitiveAtomElectronVolt + 10) < 1e-12);
assert.ok(Math.abs(primitive.metadata.calculation.forceRmsElectronVoltPerAngstrom - Math.sqrt(2.5)) < 1e-12);
assert.equal(primitive.metadata.calculation.forceMaximumElectronVoltPerAngstrom, 2);
assert.deepEqual(primitive.atoms[0].calculationForceEvPerAngstrom, [0, 1, 0]);
assert.deepEqual(primitive.atoms[1].calculationForceEvPerAngstrom, [0, 0, -2]);
assert.equal(primitive.metadata.calculation.forcesUsedForGrowth, false);
assert.equal(primitive.metadata.calculation.absoluteEnergyComparedAcrossEntries, false);

const expanded = makeLearningSupercell(primitive);
assert.ok(expanded.atoms.length >= 128 && expanded.atoms.length <= 512);
assert.equal(expanded.atoms.length, 128);
assert.deepEqual(expanded.metadata.repetitions, [4, 4, 4]);
assert.ok(Math.abs(expanded.cell[0][0] - 22.56) < 1e-12);
assert.deepEqual(expanded.atoms[2].calculationForceEvPerAngstrom, [0, 1, 0]);

const calls = [];
const fakeFetch = async (url, options) => {
  calls.push({ url, body: JSON.parse(options.body) });
  const value = url.endsWith("/entries/query")
    ? { pagination: { total: 1 }, data: [entry] }
    : archive;
  return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
};
const sampled = await randomNomadStructure(["Na", "Cl"], { fetchImpl: fakeFetch, random: () => 0 });
assert.equal(sampled.total, 1);
assert.equal(sampled.structure.atoms.length, 128);
assert.equal(calls.length, 2);
assert.equal(calls[0].body.query.and[1]["results.material.n_elements"], 2);
assert.deepEqual(calls[1].body.required.run["system[-1]"], { atoms: "*" });
assert.deepEqual(calls[1].body.required.run["calculation[-1]"], {
  energy: "*", forces: "*", system_ref: "*", method_ref: "*",
});

console.log("materials online database: conversion and supercell checks passed");
