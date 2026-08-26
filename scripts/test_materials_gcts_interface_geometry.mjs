import assert from "node:assert/strict";
import { interfaceAccommodationScore, interfaceGeometryAudit } from "../apps/iqc-growth-live/interface-geometry.js";

const positions = [[-2, 0, 0], [2, 0, 0], [-.25, -1, 0], [.25, 1, 0], [0, 0, .5]];
const species = ["Na", "Na", "Cl", "Cl", "Na"];
const memberships = [[1], [2], [1, 2], [1, 2], [1, 2]];
const audit = interfaceGeometryAudit({ positions, species, memberships,
  firstNucleusId: 1, secondNucleusId: 2, firstCenter: [-2, 0, 0], secondCenter: [2, 0, 0],
  lengthScale: 2, contactCutoff: () => 2.1 });
assert.equal(audit.sharedSiteCount, 3);
assert.equal(audit.axisDefined, true);
assert.equal(audit.centerSeparation, 8);
assert.equal(audit.axialCentroidOffset, 0);
assert.ok(Math.abs(audit.axialThicknessRms - Math.sqrt(1 / 6)) < 1e-12);
assert.equal(audit.axialSpan, 1);
assert.deepEqual(audit.chemistry, { Cl: 2, Na: 1 });
assert.equal(audit.componentCount, 1);
assert.equal(audit.registryTopology, "connected registry patch");
assert.equal(audit.profile.reduce((sum, value) => sum + value, 0), 3);
assert.equal(audit.coordinateFrameUsed, false);
assert.equal(audit.interfacialEnergyInferred, false);

const rotated = positions.map(([x, y, z]) => [-y + 4, x - 7, z + 3]);
const transformed = interfaceGeometryAudit({ positions: rotated, species, memberships,
  firstNucleusId: 1, secondNucleusId: 2, firstCenter: [4, -9, 3], secondCenter: [4, -5, 3],
  lengthScale: 2, contactCutoff: () => 2.1 });
for (const field of ["centerSeparation", "axialCentroidOffset", "axialThicknessRms",
  "axialSpan", "tangentialRadiusRms", "tangentialRadiusMaximum"]) {
  assert.ok(Math.abs(transformed[field] - audit[field]) < 1e-12, field);
}
assert.deepEqual(transformed.profile, audit.profile);
assert.deepEqual(transformed.chemistry, audit.chemistry);

const coherent = interfaceAccommodationScore({ newlyRegisteredSites: 4, componentCount: 1,
  properMisorientationDegrees: 0, comparable: true });
const fragmented = interfaceAccommodationScore({ newlyRegisteredSites: 1, componentCount: 5,
  properMisorientationDegrees: 75, comparable: true });
const noContact = interfaceAccommodationScore({ newlyRegisteredSites: 0, componentCount: 0,
  properMisorientationDegrees: null, comparable: false });
assert.ok(coherent.score > fragmented.score);
assert.ok(fragmented.score >= -1 && fragmented.score <= 1);
assert.equal(noContact.score, 0);

console.log("nucleus-interface geometry audit: passed", {
  thickness: audit.axialThicknessRms, tangentialRms: audit.tangentialRadiusRms,
  chemistry: audit.chemistry, coherentAccommodation: coherent.score,
});
