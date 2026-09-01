import assert from "node:assert/strict";
import { buildCriticalNucleusCoverVisualization } from "./critical-nucleus-cover-visualization.mjs";

const geometry = { schema: "gcts-critical-nucleus-geometry-evidence-v1", targetUsed: false,
  sites: [
    { siteId: "A", species: "Na", region: "core", membershipProbability: .9, positionAngstrom: [0, 0, 0] },
    { siteId: "B", species: "Cl", region: "core", membershipProbability: .9, positionAngstrom: [1, 0, 0] },
    { siteId: "C", species: "Na", region: "interface", membershipProbability: .7, positionAngstrom: [0, 1, 0] },
    { siteId: "D", species: "Cl", region: "interface", membershipProbability: .7, positionAngstrom: [1, 1, 1] },
    { siteId: "E", species: "Na", region: "interface", membershipProbability: .6, positionAngstrom: [2, 1, 0] },
  ] };
const event = { sites: geometry.sites.map(site => ({ ...site,
  localRotatedPositionAngstrom: [site.positionAngstrom[1], -site.positionAngstrom[0], site.positionAngstrom[2]] })) };
const admission = { targetUsed: false, candidateSetInspected: false,
  selectedOccurrences: [
    { occurrenceId: "N1", typeId: 2, supportSiteIndices: [0, 1, 2, 3], outgoingRuleCount: 3 },
    { occurrenceId: "N2", typeId: 7, supportSiteIndices: [2, 3], outgoingRuleCount: 0 },
  ],
  admittedConnectionEdges: [{ firstOccurrenceId: "N1", secondOccurrenceId: "N2",
    sharedAtoms: 2, forwardAdmitted: true, reverseAdmitted: false }],
  residualSites: [{ siteIndex: 4 }] };

const audit = buildCriticalNucleusCoverVisualization(geometry, event, admission);
assert.equal(audit.recognizedAtomCount, 4);
assert.equal(audit.residualAtomCount, 1);
assert.equal(audit.frontierOccurrenceCount, 1);
assert.deepEqual(audit.atoms[2].typeIds, [2, 7]);
assert.equal(audit.atoms[4].residual, true);
assert.equal(audit.occurrences[0].hullSiteIndices.length, 4);
assert.equal(audit.edges.length, 1);
assert.equal(audit.targetUsed, false);
assert.equal(audit.candidateSetChanged, false);

assert.throws(() => buildCriticalNucleusCoverVisualization(geometry, event,
  { ...admission, targetUsed: true }), /target-blind/);
assert.throws(() => buildCriticalNucleusCoverVisualization(geometry, { sites: event.sites.slice(1) },
  admission), /preserve every/);
assert.throws(() => buildCriticalNucleusCoverVisualization(geometry, event,
  { ...admission, residualSites: [{ siteIndex: 3 }, { siteIndex: 4 }] }), /partition/);

console.log("critical nucleus cover visualization: all tests passed");
