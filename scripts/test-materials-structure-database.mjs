import assert from "node:assert/strict";
import { canonicalElement, makeLearningSupercell, nomadArchiveToStructure, queryPayload, randomNomadBinary } from "../apps/iqc-growth-live/structure-database.js";

assert.equal(canonicalElement("na"), "Na");
assert.throws(() => canonicalElement("Xx"), /Unknown element/);
assert.throws(() => canonicalElement(""), /Unknown element/);

const payload = queryPayload("Na", "Cl", 17);
assert.deepEqual(payload.query.and[0]["results.material.elements"].all, ["Na", "Cl"]);
assert.equal(payload.query.and[1]["results.material.n_elements"], 2);
assert.equal(payload.query.and[2]["results.material.structural_type"], "bulk");
assert.equal(payload.pagination.page_offset, 17);

const entry = {
  entry_id: "test-entry",
  results: { material: {
    material_id: "test-material", elements: ["Cl", "Na"], chemical_formula_reduced: "ClNa",
    symmetry: { crystal_system: "cubic", space_group_number: 225, space_group_symbol: "Fm-3m" },
  } },
};
const archive = { data: { archive: { run: [{ system: [{ atoms: {
  labels: ["Na", "Cl"],
  positions: [[0, 0, 0], [2.82e-10, 0, 0]],
  lattice_vectors: [[5.64e-10, 0, 0], [0, 5.64e-10, 0], [0, 0, 5.64e-10]],
  periodic: [true, true, true],
} }] }] } } };
const primitive = nomadArchiveToStructure(entry, archive);
assert.ok(Math.abs(primitive.atoms[1].position[0] - 2.82) < 1e-12);
assert.equal(primitive.metadata.spaceGroupNumber, 225);
assert.equal(primitive.metadata.materialId, "test-material");

const expanded = makeLearningSupercell(primitive);
assert.ok(expanded.atoms.length >= 128 && expanded.atoms.length <= 512);
assert.equal(expanded.atoms.length, 128);
assert.deepEqual(expanded.metadata.repetitions, [4, 4, 4]);
assert.ok(Math.abs(expanded.cell[0][0] - 22.56) < 1e-12);

const calls = [];
const fakeFetch = async (url, options) => {
  calls.push({ url, body: JSON.parse(options.body) });
  const value = url.endsWith("/entries/query")
    ? { pagination: { total: 1 }, data: [entry] }
    : archive;
  return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
};
const sampled = await randomNomadBinary("Na", "Cl", { fetchImpl: fakeFetch, random: () => 0 });
assert.equal(sampled.total, 1);
assert.equal(sampled.structure.atoms.length, 128);
assert.equal(calls.length, 2);
assert.equal(calls[0].body.query.and[1]["results.material.n_elements"], 2);
assert.deepEqual(calls[1].body.required.run["system[-1]"], { atoms: "*" });

console.log("materials online database: conversion and supercell checks passed");
