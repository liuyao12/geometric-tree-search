import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  buildRruffExperimentalResponse,
  findRruffPowderProfiles,
  loadRruffPowderLibrary,
  rruffRequestCompatibility,
  RRUFF_LIBRARY_ASSET_SHA256,
} from "./public-powder-profile-library.mjs";

const bytes = await readFile(new URL("./data/rruff-powder-profiles-v1.json", import.meta.url));
const library = await loadRruffPowderLibrary({ fetchImpl: async () => ({
  ok: true, status: 200, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
}) });
assert.equal(library.assetSha256, RRUFF_LIBRARY_ASSET_SHA256);
assert.equal(library.profileCount, 15);
assert.equal(library.license, "CC BY 4.0");

const request = {
  requestId: "powder-test", structureSha256: "a".repeat(64), materialLabel: "NaCl rocksalt",
  species: ["Na", "Cl"], probe: "x-ray", modelChannel: { kind: "constant-Z", species: null },
};
const halite = findRruffPowderProfiles(library, request);
assert.equal(halite.length, 3);
assert.ok(halite.every(match => match.correspondence.level === "exact-phase"));
assert.deepEqual(halite.map(match => match.record.rruffId), ["R070292", "R070534", "R070586"]);
assert.equal(halite[0].record.wavelengthAngstrom, 1.541838);
assert.equal(halite[0].record.x.length, 8501);

const response = buildRruffExperimentalResponse(request, halite[0], library);
assert.equal(response.axis, "two-theta-degree");
assert.equal(response.independentOfGrowth, true);
assert.equal(response.usedForGrowth, false);
assert.equal(response.materialCorrespondence.sameMaterialClaimAllowed, true);
assert.match(response.provenance.title, /Halite R070292/);

const carbon = findRruffPowderProfiles(library, { ...request, species: ["C"], materialLabel: "graphene monolayer" });
assert.equal(carbon.length, 1);
assert.equal(carbon[0].record.phase, "Graphite");
assert.equal(carbon[0].correspondence.level, "composition-only");
assert.equal(carbon[0].correspondence.sameMaterialClaimAllowed, false);

assert.equal(rruffRequestCompatibility(request).compatible, true);
assert.equal(rruffRequestCompatibility({ ...request, probe: "neutron" }).compatible, false);
assert.equal(rruffRequestCompatibility({ ...request, modelChannel: { kind: "unit" } }).compatible, false);
assert.throws(() => buildRruffExperimentalResponse({ ...request, species: ["Si"] }, halite[0], library), /chemistry/);

console.log("public RRUFF powder-profile library: all tests passed");
