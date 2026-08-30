import assert from "node:assert/strict";
import { bindValidatedForceGeometry, buildValidatedForceGeometryRuntime }
  from "../apps/iqc-growth-live/external-force-geometry.mjs";

const audit = {
  quantityId: "forces", configurationRole: "observation", validationPassed: true,
  targetCoordinatesEmbedded: false, configurationSha256: "a".repeat(64), requestSha256: "b".repeat(64),
  method: { family: "DFT", program: "solver", version: "1", settingsSha256: "c".repeat(64) },
};
const response = { results: {
  forceVectorsElectronVoltPerAngstrom: [[3, 0, 0], [0, 4, 0]],
  totalEnergyElectronVolt: -10,
  stressTensorGigaPascal: [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
} };
const runtime = buildValidatedForceGeometryRuntime(response, audit, "d".repeat(64));
assert.equal(runtime.calculationProvenance.forceVectorCount, 2);
assert.equal(runtime.calculationProvenance.forceRmsElectronVoltPerAngstrom, Math.sqrt(12.5));
assert.equal(runtime.calculationProvenance.stressHydrostaticGigaPascal, 2);
assert.equal(runtime.calculationProvenance.usedAsPotential, false);

const atoms = [{ species: "A" }, { species: "B" }];
const binding = bindValidatedForceGeometry(atoms, runtime);
assert.deepEqual(atoms.map((atom) => atom.calculationForceEvPerAngstrom), [[3, 0, 0], [0, 4, 0]]);
assert.equal(binding.boundSites, 2);
assert.equal(binding.properPoseTransport, "F_world = R_cluster F_local");
assert.equal(binding.forceIntegrated, false);

assert.throws(() => bindValidatedForceGeometry([{ species: "A" }], runtime), /count no longer matches/);
assert.throws(() => buildValidatedForceGeometryRuntime(response,
  { ...audit, targetCoordinatesEmbedded: true }, "d".repeat(64)), /target-free/);

console.log("external force geometry contract: passed");
