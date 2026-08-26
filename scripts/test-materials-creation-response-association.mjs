import assert from "node:assert/strict";
import { buildCreationResponseAssociation }
  from "../apps/iqc-growth-live/creation-response-association.js";

const records = Array.from({ length: 6 }, (_, index) => ({
  placementId: index + 1, emittedSites: index % 2 ? 5 : 2,
  physicsTerms: [
    { id: "strain", label: "contact + angle", weight: -.2, contribution: index },
    { id: "loop", label: "loop closure", weight: .3, contribution: 5 - index },
    { id: "inactive", weight: 0, contribution: 99 },
  ],
  outcomes: { nonaffine: 2 * index, shellChange: index < 3 ? 0 : 1 },
}));
const audit = buildCreationResponseAssociation(records);
assert.equal(audit.available, true);
assert.equal(audit.placementSamples, 6);
assert.equal(audit.emittedSitePresentations, 21);
assert.equal(audit.atomLevelPseudoreplicationAvoided, true);
assert.equal(audit.independentMaterialSamples, false);
assert.equal(audit.termIds.includes("inactive"), false);
const positive = audit.associations.find((entry) => entry.termId === "strain" && entry.outcomeId === "nonaffine");
const negative = audit.associations.find((entry) => entry.termId === "loop" && entry.outcomeId === "nonaffine");
assert.equal(positive.spearmanRho, 1);
assert.equal(negative.spearmanRho, -1);
assert.equal(positive.points.length, 6);
assert.throws(() => buildCreationResponseAssociation([...records, records[0]]), /exactly once/);
assert.equal(buildCreationResponseAssociation(records.slice(0, 3), { minimumSamples: 4 }).available, false);
console.log("materials creation-response association: passed");
