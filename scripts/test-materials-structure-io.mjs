import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  occupancyChemistryToken,
  occupancyDisplayLabel,
  formalChargeFromChemistryToken,
  isotropicPairDistanceUncertaintyA,
  parseStructureText,
  symmetricTensorEigenSystem,
  validateStructure,
} from "../apps/iqc-growth-live/structure-io.js";

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
_diffrn_ambient_temperature 100(2)
_diffrn_ambient_pressure 101.325
_diffrn_ambient_environment 'helium exchange gas'
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
assert.deepEqual(parsedCif.metadata.measurementConditions, {
  temperature: { value: 100, sourceTag: "_diffrn_ambient_temperature", deprecatedFallback: false, unit: "K" },
  pressure: { value: 101.325, sourceTag: "_diffrn_ambient_pressure", deprecatedFallback: false, unit: "kPa" },
  environment: { value: "helium exchange gas", sourceTag: "_diffrn_ambient_environment" },
  provenance: "recorded diffraction/cell-measurement conditions",
  usedAsSimulationControl: false,
  synthesisConditionsClaimed: false,
  thermodynamicStateReconstructed: false,
});
assert.ok(parsedCif.atoms.every((atom) => atom.species === "Si"));
const parsedCifValidation = validateStructure(parsedCif);
assert.equal(parsedCifValidation.valid, true);
assert.equal(parsedCifValidation.measurementConditionsPresent, true);
assert.equal(parsedCifValidation.measurementTemperatureKelvin, 100);
assert.equal(parsedCifValidation.measurementPressureKilopascal, 101.325);
assert.equal(parsedCifValidation.measurementEnvironment, "helium exchange gas");
assert.ok(parsedCifValidation.warnings.some((warning) => warning.includes("provenance only")));

const legacyConditionsCif = cif
  .replace("_diffrn_ambient_temperature 100(2)", "_cell_measurement_temperature 95")
  .replace("_diffrn_ambient_pressure 101.325", "_cell_measurement_pressure 98.4")
  .replace("_diffrn_ambient_environment 'helium exchange gas'", "");
const legacyConditions = parseStructureText(legacyConditionsCif, "legacy-conditions.cif");
assert.equal(legacyConditions.metadata.measurementConditions.temperature.deprecatedFallback, true);
assert.equal(legacyConditions.metadata.measurementConditions.pressure.deprecatedFallback, true);
assert.equal(legacyConditions.metadata.measurementConditions.temperature.sourceTag, "_cell_measurement_temperature");
assert.equal(legacyConditions.metadata.measurementConditions.pressure.sourceTag, "_cell_measurement_pressure");
assert.throws(() => parseStructureText(cif.replace("100(2)", "-1"), "negative-temperature.cif"), /must be nonnegative/);

const oxidationCif = `data_sodium_chloride_charges
_cell_length_a 5.64
_cell_length_b 5.64
_cell_length_c 5.64
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_atom_type_symbol
_atom_type_oxidation_number
Na1 1
Cl1 -1
loop_
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Na1 0 0 0
Cl1 .5 .5 .5
`;
const chargedNacl = parseStructureText(oxidationCif, "charged-nacl.cif");
assert.deepEqual(chargedNacl.atoms.map(occupancyChemistryToken), ["Na^+1", "Cl^-1"]);
const chargedNaclValidation = validateStructure(chargedNacl);
assert.equal(chargedNaclValidation.formalChargeCoverage, 1);
assert.equal(chargedNaclValidation.netFormalCharge, 0);

const disorderedCif = await readFile(new URL("../apps/iqc-growth-live/fixtures/tav-disordered.cif", import.meta.url), "utf8");
const disorder = parseStructureText(disorderedCif, "tav.cif");
assert.equal(disorder.atoms.length, 3, "co-located alternatives must be one site; inversion creates two O sites");
const mixed = disorder.atoms.find((atom) => atom.occupancyAlternatives.length === 2);
assert.deepEqual(mixed.occupancyAlternatives, [
  { species: "Ta", fraction: .6, formalCharge: 5 },
  { species: "V", fraction: .4, formalCharge: 5 },
]);
assert.equal(occupancyChemistryToken(mixed), "occ[Ta^+5=0.6;V^+5=0.4]");
assert.equal(occupancyDisplayLabel(mixed), "Ta(+5) 60% / V(+5) 40%");
const partial = disorder.atoms.find((atom) => atom.species === "O");
assert.equal(occupancyChemistryToken(partial), "occ[O^-2=0.5;Vac=0.5]");
const disorderValidation = validateStructure(disorder);
assert.equal(disorderValidation.valid, true);
assert.equal(disorderValidation.mixedOccupancySites, 1);
assert.equal(disorderValidation.partialOccupancySites, 2);
assert.deepEqual(disorderValidation.elementCounts, { Ta: .6, V: .4, O: 1 });
assert.equal(disorderValidation.vacancyFraction, 1);
assert.equal(disorderValidation.formalChargeCoverage, 1);
assert.equal(disorderValidation.netFormalCharge, 3);
assert.equal(formalChargeFromChemistryToken(occupancyChemistryToken(mixed)), 5);
assert.equal(formalChargeFromChemistryToken(occupancyChemistryToken(partial)), -1);
assert.equal(formalChargeFromChemistryToken("O"), null);
assert.equal(disorderValidation.thermalDisplacementSites, 3);
assert.ok(Math.abs(mixed.uIsoA2 - .014) < 1e-12, "co-located alternatives use occupancy-weighted Uiso");
assert.ok(Math.abs(partial.uIsoA2 - .0175) < 1e-12, "anisotropic Ueq is trace(U)/3");
assert.deepEqual(partial.thermalSigmaAxesA.map((value) => Number(value.toFixed(8))), [.2, .1, .05]);
assert.equal(disorderValidation.anisotropicDisplacementSites, 2);
assert.ok(Math.abs(disorderValidation.maximumThermalAxisSigmaA - .2) < 1e-12);
assert.ok(Math.abs(disorderValidation.medianThermalSigmaA - Math.sqrt(.0175)) < 1e-12);
assert.ok(Math.abs(isotropicPairDistanceUncertaintyA(.1) - Math.sqrt(.02)) < 1e-12);
assert.throws(() => isotropicPairDistanceUncertaintyA(-.1), /nonnegative/);
const rotatedTensor = symmetricTensorEigenSystem([[.025, .015, 0], [.015, .025, 0], [0, 0, .01]]);
assert.deepEqual(rotatedTensor.eigenvaluesA2.map((value) => Number(value.toFixed(8))), [.04, .01, .01]);
assert.throws(() => symmetricTensorEigenSystem([[.01, .02, 0], [.02, .01, 0], [0, 0, .01]]), /positive semidefinite/);

const rotatedAnisoCif = `data_rotated_aniso
_cell_length_a 5
_cell_length_b 5
_cell_length_c 5
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_space_group_symop_operation_xyz
'x,y,z'
'-y,x,z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C1 C .2 .1 .3
loop_
_atom_site_aniso_label
_atom_site_aniso_U_11
_atom_site_aniso_U_22
_atom_site_aniso_U_33
_atom_site_aniso_U_12
_atom_site_aniso_U_13
_atom_site_aniso_U_23
C1 .04 .01 .0025 0 0 0
`;
const rotatedAniso = parseStructureText(rotatedAnisoCif, "rotated-aniso.cif");
assert.equal(rotatedAniso.atoms.length, 2);
assert.deepEqual(rotatedAniso.atoms[0].thermalSigmaAxesA.map((value) => Number(value.toFixed(8))), [.2, .1, .05]);
assert.ok(Math.abs(rotatedAniso.atoms[1].uAnisoCartesianA2[0][0] - .01) < 1e-12);
assert.ok(Math.abs(rotatedAniso.atoms[1].uAnisoCartesianA2[1][1] - .04) < 1e-12);

const hexAnisoCif = `data_hex_aniso
_cell_length_a 5
_cell_length_b 5
_cell_length_c 6
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 120
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C1 C .2 .1 .3
loop_
_atom_site_aniso_label
_atom_site_aniso_U_11
_atom_site_aniso_U_22
_atom_site_aniso_U_33
_atom_site_aniso_U_12
_atom_site_aniso_U_13
_atom_site_aniso_U_23
C1 .01 .01 .01 .005 0 0
`;
const hexAniso = parseStructureText(hexAnisoCif, "hex-aniso.cif");
const hexTensor = hexAniso.atoms[0].uAnisoCartesianA2;
assert.ok(Math.abs(hexTensor[0][0] - .01) < 1e-12 && Math.abs(hexTensor[1][1] - .01) < 1e-12);
assert.ok(Math.abs(hexTensor[0][1]) < 1e-12, "cell-metric conversion must make the hexagonal tensor Cartesian-isotropic");

const composite = parseStructureText(JSON.stringify({ atoms: [
  { species: "Ta/V", position: [0, 0, 0] },
  { species: "O", occupancy: { O: .75 }, position: [2, 0, 0] },
  { species: "O1A", position: [0, 2, 0] },
  { species: "C", position: [2, 2, 0], bIsoA2: .789568 },
  { species: "Fe2+/Fe3+", position: [3, 0, 0] },
  { species: "Fe+2/Fe+3", position: [4, 0, 0] },
] }), "occupancy.json");
assert.equal(occupancyChemistryToken(composite.atoms[0]), "occ[Ta=0.5;V=0.5]");
assert.equal(composite.atoms[0].occupancyFractionsInferred, true);
assert.equal(occupancyChemistryToken(composite.atoms[1]), "occ[O=0.75;Vac=0.25]");
assert.equal(occupancyChemistryToken(composite.atoms[2]), "O", "ordinary CIF-style atom labels must not invent an A alternative");
assert.ok(Math.abs(composite.atoms[3].uIsoA2 - .01) < 2e-8, "Biso converts to Uiso through B=8π²U");
assert.equal(occupancyChemistryToken(composite.atoms[4]), "occ[Fe^+2=0.5;Fe^+3=0.5]");
assert.equal(formalChargeFromChemistryToken(occupancyChemistryToken(composite.atoms[4])), 2.5);
assert.equal(occupancyChemistryToken(composite.atoms[5]), "occ[Fe^+2=0.5;Fe^+3=0.5]");
assert.throws(() => parseStructureText(JSON.stringify({ atoms: [
  { species: "O", position: [0, 0, 0], uIsoA2: -.01 },
] }), "negative-u.json"), /must be nonnegative/);

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

const trajectoryXyz = `${xyz}3
Lattice="8.1 0 0 0 8.1 0 0 0 8.1" pbc="T T T" water t=1
O 0.02 0 0
H 0.98 0.01 0
H -0.23 0.92 0.01
`;
const parsedTrajectory = parseStructureText(trajectoryXyz, "water-trajectory.extxyz");
assert.equal(parsedTrajectory.frames.length, 2);
assert.equal(parsedTrajectory.frames[1].atoms[0].position[0], .02);
const trajectoryValidation = validateStructure(parsedTrajectory);
assert.equal(trajectoryValidation.valid, true);
assert.equal(trajectoryValidation.trajectoryFrameCount, 2);
assert.equal(trajectoryValidation.trajectoryTopologyConsistent, true);
assert.equal(trajectoryValidation.trajectoryVariableCell, true);
assert.equal(trajectoryValidation.trajectoryAtomPresentations, 6);
const presentationLimited = validateStructure(parsedTrajectory, { maximumAtomPresentations: 5 });
assert.equal(presentationLimited.valid, false);
assert.ok(presentationLimited.errors.some((error) => error.includes("atom presentations exceed")));

const trajectoryJson = parseStructureText(JSON.stringify({
  name: "charged NaCl trajectory",
  species: ["Na", "Cl"],
  formalCharges: [1, -1],
  cell: [[5.64, 0, 0], [0, 5.64, 0], [0, 0, 5.64]],
  frames: [
    { positions: [[0, 0, 0], [2.82, 2.82, 2.82]] },
    { positions: [[.01, 0, 0], [2.81, 2.82, 2.82]] },
  ],
}), "charged-trajectory.json");
assert.equal(trajectoryJson.frames.length, 2);
assert.deepEqual(trajectoryJson.frames[1].atoms.map(occupancyChemistryToken), ["Na^+1", "Cl^-1"]);
assert.equal(validateStructure(trajectoryJson).trajectoryTopologyConsistent, true);

const changingTopology = parseStructureText(`2
frame 1
Na 0 0 0
Cl 2 0 0
2
frame 2
Na 0 0 0
Br 2 0 0
`, "changing.xyz");
assert.equal(validateStructure(changingTopology).valid, false);
assert.ok(validateStructure(changingTopology).errors.some((error) => error.includes("changes atom count, order, species")));

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
