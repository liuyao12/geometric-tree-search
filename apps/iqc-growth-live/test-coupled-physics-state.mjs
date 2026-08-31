import assert from "node:assert/strict";
import { buildCoupledPhysicsState, coupledStateGate, coupledStateFingerprint }
  from "./coupled-physics-state.mjs";

const state = "a".repeat(64); const fluxEvidence = "b".repeat(64); const eventEvidence = "c".repeat(64);
const ready = buildCoupledPhysicsState({ mode: "event",
  interfaceTransport: { validated: true, currentGeometry: true, couplingStateSha256: state,
    evidenceSha256: fluxEvidence, temperatureKelvin: 900 },
  eventKinetics: { validated: true, couplingStateSha256: state,
    evidenceSha256: eventEvidence, temperatureKelvin: 900 } });
assert.equal(ready.compatible, true);
assert.equal(coupledStateGate(ready, { strict: true }).allowed, true);
assert.equal(ready.sharedTemperatureKelvin, 900);
const mismatch = buildCoupledPhysicsState({ mode: "event",
  interfaceTransport: { validated: true, couplingStateSha256: state, evidenceSha256: fluxEvidence },
  eventKinetics: { validated: true, couplingStateSha256: "d".repeat(64), evidenceSha256: eventEvidence } });
assert.equal(mismatch.compatible, false);
assert.ok(mismatch.mismatches.includes("coupling-state-digest-mismatch"));
assert.equal(coupledStateGate(mismatch, { strict: true }).allowed, false);
const absent = buildCoupledPhysicsState({ mode: "event",
  interfaceTransport: { validated: true, couplingStateSha256: state },
  eventKinetics: { validated: true } });
assert.ok(absent.mismatches.includes("event:missing-state-digest"));
const diagnostic = buildCoupledPhysicsState({ mode: "structural" });
assert.equal(coupledStateGate(diagnostic, { strict: false }).allowed, true);
assert.equal(diagnostic.geometryUsedAsThermodynamicState, false);
assert.equal(coupledStateFingerprint({ b: 2, a: 1 }), coupledStateFingerprint({ a: 1, b: 2 }));
console.log("coupled physics-state tests passed");
