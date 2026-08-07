import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { parseStructureText, validateStructure } from "../apps/iqc-growth-live/structure-io.js";

const poscar = `NaCl conventional cell
1.0
5.64 0 0
0 5.64 0
0 0 5.64
Na Cl
1 1
Direct
0 0 0
0.5 0.5 0.5
`;
const parsedPoscar = parseStructureText(poscar, "POSCAR");
assert.equal(parsedPoscar.format, "POSCAR");
assert.deepEqual(parsedPoscar.atoms.map((atom) => atom.species), ["Na", "Cl"]);
assert.deepEqual(parsedPoscar.atoms[1].position, [2.82, 2.82, 2.82]);
assert.equal(validateStructure(parsedPoscar).valid, true);

const cif = `data_silicon
_chemical_name_common 'silicon test'
_cell_length_a 5.43
_cell_length_b 5.43
_cell_length_c 5.43
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_space_group_symop_operation_xyz
'x,y,z'
'-x,-y,-z'
loop_
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Si 0.125 0.125 0.125
`;
const parsedCif = parseStructureText(cif, "silicon.cif");
assert.equal(parsedCif.format, "CIF");
assert.equal(parsedCif.atoms.length, 2);
assert.equal(parsedCif.metadata.symmetryOperations, 2);
assert.ok(parsedCif.atoms.every((atom) => atom.species === "Si"));
assert.equal(validateStructure(parsedCif).valid, true);

const xyz = `3
Lattice="8 0 0 0 8 0 0 0 8" pbc="T T T" water
O 0 0 0
H 0.96 0 0
H -0.24 0.93 0
`;
const parsedXyz = parseStructureText(xyz, "water.extxyz");
assert.equal(parsedXyz.format, "extended XYZ");
assert.deepEqual(parsedXyz.pbc, [true, true, true]);
assert.equal(parsedXyz.atoms.length, 3);
assert.ok(validateStructure(parsedXyz).warnings.some((warning) => warning.includes("Fewer than 16 atoms")));

const fixtureText = await readFile(new URL("../apps/iqc-growth-live/fixtures/nacl-64.extxyz", import.meta.url), "utf8");
const fixture = parseStructureText(fixtureText, "nacl-64.extxyz");
const fixtureValidation = validateStructure(fixture);
assert.equal(fixture.atoms.length, 64);
assert.deepEqual(fixtureValidation.elementCounts, { Na: 32, Cl: 32 });
assert.ok(Math.abs(fixtureValidation.medianNearestDistance - 2.82) < 1e-10);
assert.equal(fixtureValidation.valid, true);

const json = JSON.stringify({
  name: "bcc Fe",
  cell: [[2.87, 0, 0], [0, 2.87, 0], [0, 0, 2.87]],
  pbc: [true, true, true],
  species: ["Fe", "Fe"],
  positions: [[0, 0, 0], [1.435, 1.435, 1.435]],
});
const parsedJson = parseStructureText(json, "iron.json");
assert.equal(parsedJson.atoms.length, 2);
assert.equal(validateStructure(parsedJson).valid, true);

const duplicate = parseStructureText(JSON.stringify({
  atoms: [{ species: "C", position: [0, 0, 0] }, { species: "C", position: [0.01, 0, 0] }],
}), "duplicate.json");
assert.equal(validateStructure(duplicate).valid, false);

console.log("materials structure I/O: all parser and validation checks passed");
