import assert from "node:assert/strict";
import { archivedResponseDeformationGradient, archivedStressStrainResponseArtifact,
  fitArchivedStressStrainResponse }
  from "../apps/iqc-growth-live/stress-strain-response.js";

const diagonalCell = (scale, shear = 0) => [[scale, 0, 0], [shear, scale * .98, 0], [0, 0, scale * 1.02]];
const referenceCell = diagonalCell(5);
const frames = Array.from({ length: 7 }, (_, index) => {
  const hydro = (6 - index) * .4;
  const shear = (6 - index) * .08;
  const cellScale = 5 / (1 + .006 * hydro);
  return {
    cell: index === 6 ? referenceCell : diagonalCell(cellScale, -.01 * shear),
    stressTensorGigaPascal: [[-hydro, -shear, 0], [-shear, -hydro, 0], [0, 0, -hydro]],
  };
});
const fit = fitArchivedStressStrainResponse(frames);
assert.equal(fit.available, true);
assert.equal(fit.recordCount, 6);
assert.equal(fit.complianceChannelsSameSign, true);
assert.ok(fit.crossValidatedSkill > .2);
assert.equal(fit.promotionPassed, true);
const deformation = archivedResponseDeformationGradient(fit, 0);
assert.equal(deformation.length, 3);
assert.ok(deformation[0][0] > 1);
assert.equal(fit.targetCoordinatesUsed, false);
const artifact = archivedStressStrainResponseArtifact(fit, {
  selectedFrameIndex: 0, selectedAsSoftRankingMetric: true, maximumStrain: .02,
});
assert.equal(artifact.promotionPassed, true);
assert.equal(artifact.eligiblePairCount, 6);
assert.equal(artifact.leaveOneFrameOut.length, 6);
assert.equal(artifact.selectedFrameEligible, true);
assert.equal(artifact.selectedAsSoftRankingMetric, true);
assert.equal(artifact.selectedDeformationGradient.length, 3);
assert.equal(artifact.candidateGeometryChanged, false);
assert.equal(artifact.hardAdmissionChanged, false);
assert.equal(artifact.independentValidationClaimed, false);
assert.equal(artifact.generalElasticTensorClaimed, false);
assert.deepEqual(artifact, archivedStressStrainResponseArtifact(fit, {
  selectedFrameIndex: 0, selectedAsSoftRankingMetric: true, maximumStrain: .02,
}));

const signConflict = frames.map((frame, index) => ({ ...frame,
  stressTensorGigaPascal: frame.stressTensorGigaPascal.map((row) => [...row]) }));
signConflict.forEach((frame) => { frame.stressTensorGigaPascal[0][1] *= -1; frame.stressTensorGigaPascal[1][0] *= -1; });
const rejected = fitArchivedStressStrainResponse(signConflict);
assert.equal(rejected.promotionPassed, false);
assert.equal(archivedResponseDeformationGradient(rejected, 0), null);
assert.equal(archivedStressStrainResponseArtifact(rejected, {
  selectedFrameIndex: 0, selectedAsSoftRankingMetric: true,
}).selectedDeformationGradient, null);
assert.equal(fitArchivedStressStrainResponse(frames.slice(0, 4)).available, false);

console.log("archived stress–strain response: passed");
