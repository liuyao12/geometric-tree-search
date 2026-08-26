import assert from "node:assert/strict";
import { buildSiteConstraintAudit } from "../apps/iqc-growth-live/site-constraint-audit.js";

const distanceModel = { byKey: { "H|O": { typicalContact: 1, contactScale: .1,
  lowerContact: .9, upperContact: 1.1 } } };
const coordinationModel = { records: [{ centerSpecies: "O", neighborSpecies: "H",
  medianObserved: 2, maximumObserved: 2 }], byKey: { "O>H": { contactCutoff: 1.2 } } };
const angularModel = { byKey: { "H<O>H": { bands: [{ minimum: 85, maximum: 95 }] } } };
const aggregate = { contactAngleMismatch: .05, distance: 0, angle: 0,
  coordinationDeficit: 0, contactTerms: 2, angleTerms: 1, coordinationTerms: 1, neighborCount: 2 };
const audit = buildSiteConstraintAudit({ centerSpecies: "O", neighbors: [
  { species: "H", distance: 1, vector: [1, 0, 0] },
  { species: "H", distance: 1, vector: [0, 1, 0] },
], distanceModel, coordinationModel, angularModel, aggregate,
populationContext: { comparedCenters: 10, contactAnglePercentile: 20 } });
assert.equal(audit.summary.status, "inside learned local geometry");
assert.equal(audit.distanceChannels.length, 2);
assert.equal(audit.distanceChannels[0].status, "within mode");
assert.equal(audit.coordinationChannels[0].status, "within learned range");
assert.equal(audit.angleChannels[0].observed, 90);
assert.equal(audit.angleChannels[0].status, "within band");
assert.equal(audit.targetUsed, false);
assert.equal(audit.physicalPotentialUsed, false);

const outside = buildSiteConstraintAudit({ centerSpecies: "O", neighbors: [
  { species: "H", distance: 1.19, vector: [1.19, 0, 0] },
  { species: "H", distance: 1.19, vector: [-1.19, 0, 0] },
  { species: "H", distance: 1.1, vector: [0, 1.1, 0] },
], distanceModel, coordinationModel, angularModel,
aggregate: { ...aggregate, contactAngleMismatch: 2, distance: 1.2, angle: 2,
  coordinationDeficit: 0, contactTerms: 3, angleTerms: 3, neighborCount: 3 } });
assert.equal(outside.coordinationChannels[0].status, "over capacity");
assert.ok(outside.angleChannels.some((channel) => channel.status === "outside band"));
assert.equal(outside.summary.status, "outside learned support");
assert.ok(outside.summary.hardConflicts > 0);
assert.throws(() => buildSiteConstraintAudit({ centerSpecies: "O" }), /requires/);
console.log("materials site constraint audit: passed");
