import assert from "node:assert/strict";
import { canonicalElement, loadNomadStructureCandidate, makeLearningSupercell, NOMAD_EVIDENCE_TARGETS,
  NOMAD_STRUCTURE_FAMILIES, nomadArchiveToStructure, nomadEntryCandidate,
  nomadEvidenceProfileLabel, nomadEvidenceTargetAccepts, nomadStructureEvidenceProfile,
  nomadStructureCandidates, normalizeElements, normalizeNomadEvidenceTarget, normalizeNomadStructureFamily,
  queryPayload, randomNomadStructure }
  from "../apps/iqc-growth-live/structure-database.js";
import { validateStructure } from "../apps/iqc-growth-live/structure-io.js";

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
const forcePayload = queryPayload(["Na", "Cl"], 0, "forces");
assert.equal(forcePayload.query.and[3]["results.properties.geometry_optimization.final_force_maximum:lte"], 1e6);
const stressPayload = queryPayload(["Na", "Cl"], 0, "stress");
assert.equal(stressPayload.query.and[3]["results.properties.geometry_optimization.final_force_maximum:lte"], 1e6);
const relaxationPayload = queryPayload(["Na", "Cl"], 0, "relaxation");
assert.equal(relaxationPayload.query.and[3]["results.properties.geometry_optimization.final_energy_difference:lte"], 1e6);
assert.equal(queryPayload(["Na", "Cl"], 0, "geometry").query.and.length, 3);
const twoDPayload = queryPayload(["C"], 0, "geometry", "twoD");
assert.equal(twoDPayload.query.and[2]["results.material.structural_type"], "2D");
assert.equal(twoDPayload.query.and.length, 3);
const waterPayload = queryPayload(["H", "O"], 0, "geometry", "water");
assert.equal(waterPayload.query.and[2]["results.material.structural_type"], "bulk");
assert.equal(waterPayload.query.and[3]["results.material.chemical_formula_reduced"], "H2O");
assert.equal(normalizeNomadStructureFamily("twoD"), NOMAD_STRUCTURE_FAMILIES.twoD);
assert.throws(() => normalizeNomadStructureFamily("invented"), /Unknown NOMAD structure family/);
assert.throws(() => queryPayload(["Na", "Cl"], 0, "geometry", "water"), /requires exactly H \+ O/);
assert.equal(queryPayload(["C"], 7, "geometry", "twoD", 99).pagination.page_size, 8);

const entry = {
  entry_id: "test-entry",
  results: { material: {
    material_id: "test-material", elements: ["Cl", "Na"], chemical_formula_reduced: "ClNa",
    symmetry: { crystal_system: "cubic", space_group_number: 225, space_group_symbol: "Fm-3m" },
  } },
};
const archive = { data: { archive: { run: [{ program: { name: "VASP", version: "test-version" }, method: [{ electronic: { method: "DFT" }, dft: { basis_set_type: "plane waves" } }], system: [{ atoms: {
  labels: ["Na", "Cl"],
  positions: [[0, 0, 0], [2.82e-10, 0, 0]],
  lattice_vectors: [[5.64e-10, 0, 0], [0, 5.64e-10, 0], [0, 0, 5.64e-10]],
  periodic: [true, true, true],
} }], calculation: [{ system_ref: "/run/0/system/0", method_ref: "/run/0/method/0",
  energy: { total: { value: -3.204353268e-18 } },
  forces: { total: { value: [[0, 1.602176634e-9, 0], [0, 0, -3.204353268e-9]] } },
  stress: { total: { value: [[2e9, 2e8, 0], [4e8, -1e9, 0], [0, 0, 1e9]] } },
  charges: [{ analysis_method: "Bader", spins: [1.25, -1.25] }],
}] }] } } };
const primitive = nomadArchiveToStructure(entry, archive);
assert.ok(Math.abs(primitive.atoms[1].position[0] - 2.82) < 1e-12);
assert.equal(primitive.metadata.spaceGroupNumber, 225);
assert.equal(primitive.metadata.materialId, "test-material");
assert.equal(primitive.metadata.calculation.programName, "VASP");
assert.equal(primitive.metadata.calculation.systemReference, "/run/0/system/0");
assert.equal(primitive.metadata.calculation.methodRecordAvailable, true);
assert.equal(primitive.metadata.calculation.methodCanonicalJson,
  '{"dft":{"basis_set_type":"plane waves"},"electronic":{"method":"DFT"}}');
assert.ok(Math.abs(primitive.metadata.calculation.totalEnergyElectronVolt + 20) < 1e-12);
assert.ok(Math.abs(primitive.metadata.calculation.energyPerPrimitiveAtomElectronVolt + 10) < 1e-12);
assert.ok(Math.abs(primitive.metadata.calculation.forceRmsElectronVoltPerAngstrom - Math.sqrt(2.5)) < 1e-12);
assert.equal(primitive.metadata.calculation.forceMaximumElectronVoltPerAngstrom, 2);
assert.deepEqual(primitive.metadata.calculation.stressTensorGigaPascal
  .map((row) => row.map((value) => Number(value.toFixed(12)))), [[2, .3, 0], [.3, -1, 0], [0, 0, 1]]);
assert.equal(primitive.metadata.calculation.stressCoverage, 1);
assert.equal(primitive.metadata.calculation.stressUnit, "GPa");
assert.equal(primitive.metadata.calculation.stressArchiveUnit, "Pa");
assert.equal(primitive.metadata.calculation.stressSourcePath, "run/0/calculation/0/stress/total/value");
assert.equal(primitive.metadata.calculation.stressUsedForGrowth, false);
assert.equal(primitive.metadata.calculation.stressEligibleAsNormalizedAffineMetric, true);
assert.deepEqual(primitive.atoms[0].calculationForceEvPerAngstrom, [0, 1, 0]);
assert.deepEqual(primitive.atoms[1].calculationForceEvPerAngstrom, [0, 0, -2]);
assert.equal(primitive.atoms[0].calculationSpin, 1.25);
assert.equal(primitive.atoms[1].calculationSpin, -1.25);
assert.equal(primitive.metadata.calculation.spinCoverage, 1);
assert.equal(primitive.metadata.calculation.atomicSpinCount, 2);
assert.equal(primitive.metadata.calculation.atomicSpinSourcePath, "run/0/calculation/0/charges/0/spins");
assert.equal(primitive.metadata.calculation.atomicSpinAnalysisMethod, "Bader");
assert.equal(primitive.metadata.calculation.atomicSpinUnit, null);
assert.equal(primitive.metadata.calculation.atomicSpinAxisAvailable, false);
assert.equal(primitive.metadata.calculation.atomicSpinsUsedForGrowth, false);
assert.equal(primitive.metadata.calculation.forcesUsedForGrowth, false);
assert.equal(primitive.metadata.calculation.absoluteEnergyComparedAcrossEntries, false);
const primitiveEvidence = nomadStructureEvidenceProfile(primitive);
assert.equal(primitiveEvidence.frameCount, 1);
assert.equal(primitiveEvidence.forceLabelsAvailable, true);
assert.equal(primitiveEvidence.stressLabelsAvailable, true);
assert.equal(primitiveEvidence.stressFrames, 1);
assert.equal(primitiveEvidence.relaxationAvailable, false);
assert.equal(primitiveEvidence.calibrationReady, false);
assert.equal(nomadEvidenceTargetAccepts(primitiveEvidence, "geometry"), true);
assert.equal(nomadEvidenceTargetAccepts(primitiveEvidence, "forces"), true);
assert.equal(nomadEvidenceTargetAccepts(primitiveEvidence, "stress"), true);
assert.equal(nomadEvidenceTargetAccepts(primitiveEvidence, "relaxation"), false);
assert.equal(nomadEvidenceProfileLabel(primitiveEvidence), "stress-labelled geometry · 1/1 snapshots");
assert.equal(normalizeNomadEvidenceTarget("calibration"), NOMAD_EVIDENCE_TARGETS.calibration);
assert.throws(() => normalizeNomadEvidenceTarget("invented"), /Unknown NOMAD evidence target/);

const expanded = makeLearningSupercell(primitive);
assert.ok(expanded.atoms.length >= 128 && expanded.atoms.length <= 512);
assert.equal(expanded.atoms.length, 128);
assert.deepEqual(expanded.metadata.repetitions, [4, 4, 4]);
assert.ok(Math.abs(expanded.cell[0][0] - 22.56) < 1e-12);
assert.deepEqual(expanded.atoms[2].calculationForceEvPerAngstrom, [0, 1, 0]);
assert.equal(expanded.atoms[2].calculationSpin, 1.25);

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
  energy: "*", forces: "*", stress: "*", charges: "*", system_ref: "*", method_ref: "*",
});
assert.equal(sampled.evidenceTarget.id, "geometry");
assert.equal(sampled.evidenceProfile.forceLabelsAvailable, true);
assert.equal(sampled.structure.metadata.nomadEvidenceTarget, "geometry");
assert.equal(sampled.structure.metadata.nomadStructureFamily, "bulk");
assert.equal(sampled.structureFamily.id, "bulk");
const indexedCandidate = nomadEntryCandidate(entry);
assert.equal(indexedCandidate.formula, "ClNa");
assert.equal(indexedCandidate.spaceGroupNumber, 225);
assert.equal(indexedCandidate.indexedRelaxation, false);
assert.ok(indexedCandidate.sourceUrl.includes("/search/entries/entry/id/test-entry"));
const candidateCalls = [];
const candidateFetch = async (url, options) => {
  candidateCalls.push({ url, body: JSON.parse(options.body) });
  const value = url.endsWith("/entries/query")
    ? { pagination: { total: 4 }, data: [entry] }
    : archive;
  return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
};
const tray = await nomadStructureCandidates(["Na", "Cl"], {
  fetchImpl: candidateFetch, random: () => 0, limit: 4,
});
assert.equal(tray.total, 4);
assert.equal(tray.candidates.length, 1);
assert.equal(candidateCalls.length, 2);
assert.equal(candidateCalls[1].body.pagination.page_size, 4);
const loadedCandidate = await loadNomadStructureCandidate(tray.candidates[0], {
  fetchImpl: candidateFetch, structureFamily: "bulk", evidenceTarget: "geometry",
  candidateOffset: 2, candidateCount: 4,
});
assert.equal(loadedCandidate.structure.atoms.length, 128);
assert.equal(loadedCandidate.structure.metadata.nomadCandidateOffset, 2);
assert.equal(loadedCandidate.structure.metadata.nomadCandidateCount, 4);
const forceSampled = await randomNomadStructure(["Na", "Cl"], {
  fetchImpl: fakeFetch, random: () => 0, evidenceTarget: "forces",
});
assert.equal(forceSampled.evidenceTarget.id, "forces");
assert.equal(forceSampled.structure.metadata.nomadEvidenceLabel, "stress-labelled geometry · 1/1 snapshots");
const stressSampled = await randomNomadStructure(["Na", "Cl"], {
  fetchImpl: fakeFetch, random: () => 0, evidenceTarget: "stress",
});
assert.equal(stressSampled.evidenceTarget.id, "stress");
assert.equal(stressSampled.evidenceProfile.stressLabelsAvailable, true);
await assert.rejects(randomNomadStructure(["Na", "Cl"], {
  fetchImpl: fakeFetch, random: () => 0, evidenceTarget: "relaxation",
}), /No public .* archive matched relaxation series/);

const relaxationEntry = {
  ...entry,
  entry_id: "relaxation-entry",
  results: {
    ...entry.results,
    properties: { geometry_optimization: { final_energy_difference: 1e-22, final_force_maximum: 2e-11 } },
  },
};
const relaxationSystems = [0, 1, 2].map((step) => ({ atoms: {
  labels: ["Na", "Cl"],
  positions: [[step * .01e-10, 0, 0], [(2.90 - step * .04) * 1e-10, 0, 0]],
  lattice_vectors: [[5.8e-10 - step * .08e-10, 0, 0], [0, 5.8e-10 - step * .08e-10, 0], [0, 0, 5.8e-10 - step * .08e-10]],
  periodic: [true, true, true],
} }));
const relaxationCalculations = [-18, -19.5, -20].map((energyEv, step) => ({
  system_ref: `/run/0/system/${step}`, method_ref: "/run/0/method/0",
  energy: { total: { value: energyEv * 1.602176634e-19 } },
  forces: { total: { value: [[0, (3 - step) * 1.602176634e-9, 0], [0, 0, -(3 - step) * 1.602176634e-9]] } },
}));
const relaxationArchive = { data: { archive: { run: [{ program: { name: "VASP", version: "relax-test" },
  method: [{ electronic: { method: "DFT" }, dft: { basis_set_type: "plane waves" } }],
  system: relaxationSystems, calculation: relaxationCalculations }] } } };
const relaxation = nomadArchiveToStructure(relaxationEntry, relaxationArchive);
assert.equal(relaxation.frames.length, 3);
assert.equal(relaxation.metadata.preferredFrameIndex, 2);
assert.equal(relaxation.metadata.relaxationSequence.originalSystemCount, 3);
assert.deepEqual(relaxation.metadata.relaxationSequence.retainedSystemIndices, [0, 1, 2]);
assert.equal(relaxation.metadata.relaxationSequence.physicalTimeAvailable, false);
assert.equal(relaxation.metadata.relaxationSequence.integratedAsTrajectory, false);
assert.ok(Math.abs(relaxation.frames[0].metadata.calculation.energyPerPrimitiveAtomElectronVolt + 9) < 1e-12);
assert.ok(Math.abs(relaxation.frames[2].metadata.calculation.energyPerPrimitiveAtomElectronVolt + 10) < 1e-12);
assert.equal(relaxation.frames[1].metadata.nomadCalculationIndex, 1);
assert.deepEqual(relaxation.frames[0].atoms[0].calculationForceEvPerAngstrom, [0, 3, 0]);
assert.deepEqual(relaxation.frames[2].atoms[1].calculationForceEvPerAngstrom, [0, 0, -1]);
const relaxationEvidence = nomadStructureEvidenceProfile(relaxation);
assert.equal(relaxationEvidence.relaxationAvailable, true);
assert.equal(relaxationEvidence.relaxationFrames, 3);
assert.equal(relaxationEvidence.energyFrames, 3);
assert.equal(relaxationEvidence.forceFrames, 3);
assert.equal(relaxationEvidence.methodConsistent, true);
assert.equal(relaxationEvidence.calibrationReady, false);
assert.equal(nomadEvidenceTargetAccepts(relaxationEvidence, "relaxation"), true);
const expandedRelaxation = makeLearningSupercell(relaxation);
assert.equal(expandedRelaxation.frames.length, 3);
assert.equal(expandedRelaxation.frames[0].atoms.length, 128);
assert.equal(expandedRelaxation.frames[2].atoms.length, 128);
assert.ok(Math.abs(expandedRelaxation.frames[0].cell[0][0] - 23.2) < 1e-12);
assert.ok(Math.abs(expandedRelaxation.frames[2].cell[0][0] - 22.56) < 1e-12);
assert.deepEqual(expandedRelaxation.frames[0].atoms[2].calculationForceEvPerAngstrom, [0, 3, 0]);
assert.equal(expandedRelaxation.frames[0].atoms[2].primitiveSourceIndex, 0);
assert.deepEqual(expandedRelaxation.frames[0].atoms[2].supercellImage, [0, 0, 1]);
assert.deepEqual(expandedRelaxation.frames[0].metadata.repetitions, [4, 4, 4]);
assert.equal(expandedRelaxation.frames[0].metadata.primitiveAtomCount, 2);
const expandedRelaxationValidation = validateStructure(expandedRelaxation, { maximumAtoms: 1200 });
assert.equal(expandedRelaxationValidation.valid, true);
assert.equal(expandedRelaxationValidation.trajectoryFrameCount, 3);
assert.ok(expandedRelaxationValidation.warnings.some((warning) => warning.includes("ordered relaxation snapshots")));

const manySystems = Array.from({ length: 30 }, (_, index) => ({ atoms: {
  ...relaxationSystems[index % relaxationSystems.length].atoms,
  positions: [[index * .001e-10, 0, 0], [(2.9 - index * .001) * 1e-10, 0, 0]],
} }));
const manyCalculations = Array.from({ length: 30 }, (_, index) => ({
  ...relaxationCalculations[index % relaxationCalculations.length],
  system_ref: `/run/0/system/${index}`,
}));
const boundedRelaxation = nomadArchiveToStructure(relaxationEntry, {
  data: { archive: { run: [{ program: { name: "VASP" }, system: manySystems, calculation: manyCalculations }] } },
});
assert.equal(boundedRelaxation.frames.length, 24);
assert.equal(boundedRelaxation.metadata.relaxationSequence.originalSystemCount, 30);
assert.equal(boundedRelaxation.metadata.relaxationSequence.retainedSystemIndices[0], 0);
assert.equal(boundedRelaxation.metadata.relaxationSequence.retainedSystemIndices.at(-1), 29);

const calibrationSystems = Array.from({ length: 5 }, (_, index) => ({ atoms: {
  ...relaxationSystems[index % relaxationSystems.length].atoms,
  positions: [[index * .002e-10, 0, 0], [(2.9 - index * .02) * 1e-10, 0, 0]],
} }));
const calibrationCalculations = Array.from({ length: 5 }, (_, index) => ({
  ...relaxationCalculations[index % relaxationCalculations.length],
  system_ref: `/run/0/system/${index}`,
}));
const calibrationStructure = nomadArchiveToStructure(relaxationEntry, {
  data: { archive: { run: [{ program: { name: "VASP", version: "calibration-test" },
    method: [{ electronic: { method: "DFT" } }], system: calibrationSystems,
    calculation: calibrationCalculations }] } },
});
const calibrationEvidence = nomadStructureEvidenceProfile(calibrationStructure);
assert.equal(calibrationEvidence.relaxationFrames, 5);
assert.equal(calibrationEvidence.pairedCalculationFrames, 5);
assert.equal(calibrationEvidence.methodConsistent, true);
assert.equal(calibrationEvidence.calibrationReady, true);
assert.equal(nomadEvidenceTargetAccepts(calibrationEvidence, "calibration"), true);
assert.equal(nomadEvidenceProfileLabel(calibrationEvidence), "5 snapshots · calculation-series ready");

const relaxationCalls = [];
const relaxationFetch = async (url, options) => {
  relaxationCalls.push({ url, body: JSON.parse(options.body) });
  const value = url.endsWith("/entries/query")
    ? { pagination: { total: 1 }, data: [relaxationEntry] }
    : relaxationArchive;
  return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
};
const sampledRelaxation = await randomNomadStructure(["Na", "Cl"], { fetchImpl: relaxationFetch, random: () => 0 });
assert.equal(sampledRelaxation.structure.frames.length, 3);
assert.deepEqual(relaxationCalls[1].body.required.run.system, { atoms: "*" });
assert.deepEqual(relaxationCalls[1].body.required.run.calculation, {
  energy: "*", forces: "*", stress: "*", charges: "*", system_ref: "*", method_ref: "*",
});
assert.equal(relaxationCalls[1].body.required.run["system[-1]"], undefined);
const sampledRelaxationTarget = await randomNomadStructure(["Na", "Cl"], {
  fetchImpl: relaxationFetch, random: () => 0, evidenceTarget: "relaxation",
});
assert.equal(sampledRelaxationTarget.evidenceProfile.relaxationAvailable, true);
assert.equal(sampledRelaxationTarget.attemptedEntries, 1);

console.log("materials online database: conversion and supercell checks passed");
