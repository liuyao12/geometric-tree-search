import assert from "node:assert/strict";
import { buildSiteCreationPhysicsAudit } from "../apps/iqc-growth-live/site-creation-physics-audit.js";

const audit = buildSiteCreationPhysicsAudit({ markingScore: .75, physicsTerms: [
  { id: "strain", label: "contact + angle", raw: .4, weight: -.2, contribution: -.08,
    role: "soft geometry", claimBoundary: "not elastic energy" },
  { id: "loop", label: "loop closure", raw: .5, weight: .3, contribution: .15,
    role: "soft compatibility", claimBoundary: "not elastic energy" },
  { id: "charge", label: "formal charge", raw: .2, weight: 0, contribution: 0,
    role: "diagnostic", claimBoundary: "not electrostatic energy" },
], admissionGates: [
  { id: "collision", label: "hard core", observed: 0, passed: true, requirement: "zero conflicts" },
  { id: "support", label: "shared support", observed: 2, passed: true, requirement: "at least two" },
] });
assert.equal(audit.available, true);
assert.equal(audit.activeTerms.length, 2);
assert.equal(audit.diagnosticTerms.length, 1);
assert.equal(audit.activeTerms[0].id, "loop");
assert.equal(audit.signedContribution, .07);
assert.equal(audit.allHardGatesPassed, true);
assert.equal(audit.targetUsed, false);
assert.equal(audit.scoreIsEnergy, false);
assert.equal(audit.physicalTimeIntegrated, false);
assert.equal(buildSiteCreationPhysicsAudit(null).available, false);
assert.throws(() => buildSiteCreationPhysicsAudit({ physicsTerms: [{ id: "bad", raw: NaN }] }), /finite/);
assert.throws(() => buildSiteCreationPhysicsAudit({ physicsTerms: [], admissionGates: [{ id: "bad" }] }), /boolean/);
console.log("materials site creation physics audit: passed");
