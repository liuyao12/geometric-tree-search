import assert from "node:assert/strict";
import { buildLeapfrogPhysicsCycle, couplingModeGate, leapfrogCycleFingerprint }
  from "./leapfrog-physics-cycle.mjs";

const base = { pipelineStage: 4, targetFree: true, geometryStateDigest: "state-a",
  geometryRevision: 7, atomCount: 512, materialEvidenceCount: 2,
  interfaceTransport: { validated: false }, frontier: { available: true, candidateCount: 18 },
  eventCheckpoint: { present: false }, stateCoherence: { compatible: true, mismatches: [],
    stateFingerprint: "coherent" } };
const structural = buildLeapfrogPhysicsCycle({ ...base, mode: "structural" });
assert.equal(structural.commitReady, true);
assert.equal(structural.nextAction, "commit-structural-leap");
assert.equal(couplingModeGate(structural).allowed, true);
const voluntaryCheckpoint = buildLeapfrogPhysicsCycle({ ...base, mode: "structural",
  eventCheckpoint: { present: true, generationCurrent: true, validated: false, candidateCount: 18 } });
assert.equal(voluntaryCheckpoint.nextAction, "calculate-action-physics");

const missingFlux = buildLeapfrogPhysicsCycle({ ...base, mode: "interface" });
assert.equal(missingFlux.commitReady, false);
assert.equal(missingFlux.nextAction, "recalculate-interface-transport");
const currentFlux = { validated: true, boundStateDigest: "state-a", responseDigest: "flux-response" };
const interfaceReady = buildLeapfrogPhysicsCycle({ ...base, mode: "interface", interfaceTransport: currentFlux });
assert.equal(interfaceReady.commitReady, true);
const stale = buildLeapfrogPhysicsCycle({ ...base, mode: "interface",
  interfaceTransport: { ...currentFlux, boundStateDigest: "state-old" } });
assert.equal(stale.nodes.find((entry) => entry.id === "transport").status, "stale");

const needFreeze = buildLeapfrogPhysicsCycle({ ...base, mode: "event", interfaceTransport: currentFlux });
assert.equal(needFreeze.nextAction, "freeze-action-frontier");
const needPhysics = buildLeapfrogPhysicsCycle({ ...base, mode: "event", interfaceTransport: currentFlux,
  eventCheckpoint: { present: true, generationCurrent: true, validated: false,
    candidateCount: 18, candidateBatchDigest: "batch" } });
assert.equal(needPhysics.nextAction, "calculate-action-physics");
const needSelection = buildLeapfrogPhysicsCycle({ ...base, mode: "event", interfaceTransport: currentFlux,
  eventCheckpoint: { present: true, generationCurrent: true, validated: true, eventSelected: false,
    candidateCount: 18, candidateBatchDigest: "batch", responseDigest: "response" } });
assert.equal(needSelection.nextAction, "select-kinetic-event");
const eventReady = buildLeapfrogPhysicsCycle({ ...base, mode: "event", interfaceTransport: currentFlux,
  eventCheckpoint: { present: true, generationCurrent: true, validated: true, eventSelected: true,
    candidateCount: 18, candidateBatchDigest: "batch", responseDigest: "response" } });
assert.equal(eventReady.commitReady, true);
const incompatible = buildLeapfrogPhysicsCycle({ ...base, mode: "event", interfaceTransport: currentFlux,
  stateCoherence: { compatible: false, mismatches: ["temperature-mismatch"], stateFingerprint: "bad" },
  eventCheckpoint: { present: true, generationCurrent: true, validated: true, eventSelected: true,
    candidateCount: 18, candidateBatchDigest: "batch", responseDigest: "response" } });
assert.equal(incompatible.nextAction, "resolve-coupling-state");
assert.equal(incompatible.commitReady, false);
assert.deepEqual(eventReady.invalidationAfterCommit.invalidated,
  ["current-interface transport map", "frozen candidate batch", "candidate-resolved barriers and prefactors"]);
assert.equal(eventReady.targetUsed, false);
assert.equal(eventReady.physicalTimeIntegrated, false);
assert.equal(leapfrogCycleFingerprint({ b: 2, a: 1 }), leapfrogCycleFingerprint({ a: 1, b: 2 }));
console.log("leap-frog physics-cycle tests passed");
