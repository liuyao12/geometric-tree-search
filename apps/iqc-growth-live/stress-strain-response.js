function finiteMatrix3(value) {
  return Array.isArray(value) && value.length === 3
    && value.every((row) => Array.isArray(row) && row.length === 3
      && row.every((component) => Number.isFinite(Number(component))));
}

function matrix(value) {
  return value.map((row) => row.map(Number));
}

function identity3() {
  return [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
}

function transpose(value) {
  return value[0].map((_, column) => value.map((row) => row[column]));
}

function multiply(first, second) {
  return first.map((row) => second[0].map((_, column) =>
    row.reduce((sum, value, index) => sum + value * second[index][column], 0)));
}

function subtract(first, second) {
  return first.map((row, firstIndex) => row.map((value, secondIndex) => value - second[firstIndex][secondIndex]));
}

function addScaled(first, second, scale) {
  return first.map((row, firstIndex) => row.map((value, secondIndex) =>
    value + scale * second[firstIndex][secondIndex]));
}

function determinant(value) {
  return value[0][0] * (value[1][1] * value[2][2] - value[1][2] * value[2][1])
    - value[0][1] * (value[1][0] * value[2][2] - value[1][2] * value[2][0])
    + value[0][2] * (value[1][0] * value[2][1] - value[1][1] * value[2][0]);
}

function inverse(value) {
  const det = determinant(value);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-18) return null;
  return [
    [value[1][1] * value[2][2] - value[1][2] * value[2][1], value[0][2] * value[2][1] - value[0][1] * value[2][2], value[0][1] * value[1][2] - value[0][2] * value[1][1]],
    [value[1][2] * value[2][0] - value[1][0] * value[2][2], value[0][0] * value[2][2] - value[0][2] * value[2][0], value[0][2] * value[1][0] - value[0][0] * value[1][2]],
    [value[1][0] * value[2][1] - value[1][1] * value[2][0], value[0][1] * value[2][0] - value[0][0] * value[2][1], value[0][0] * value[1][1] - value[0][1] * value[1][0]],
  ].map((row) => row.map((component) => component / det));
}

function cellMatrix(cell) {
  if (!finiteMatrix3(cell)) return null;
  return [[cell[0][0], cell[1][0], cell[2][0]],
    [cell[0][1], cell[1][1], cell[2][1]],
    [cell[0][2], cell[1][2], cell[2][2]]].map((row) => row.map(Number));
}

function inner(first, second) {
  return first.reduce((sum, row, firstIndex) => sum + row.reduce((rowSum, value, secondIndex) =>
    rowSum + value * second[firstIndex][secondIndex], 0), 0);
}

function frobenius(value) {
  return Math.sqrt(Math.max(0, inner(value, value)));
}

function tensorParts(value) {
  const hydrostatic = (value[0][0] + value[1][1] + value[2][2]) / 3;
  const hydro = identity3().map((row) => row.map((entry) => entry * hydrostatic));
  return { hydrostatic, hydro, deviatoric: subtract(value, hydro) };
}

function responseRecord(frame, reference, frameIndex) {
  const sourceCell = cellMatrix(frame?.cell);
  const targetCell = cellMatrix(reference?.cell);
  const sourceInverse = sourceCell && inverse(sourceCell);
  const sourceStress = finiteMatrix3(frame?.stressTensorGigaPascal)
    ? matrix(frame.stressTensorGigaPascal) : null;
  const targetStress = finiteMatrix3(reference?.stressTensorGigaPascal)
    ? matrix(reference.stressTensorGigaPascal) : null;
  if (!sourceInverse || !targetCell || !sourceStress || !targetStress) return null;
  const deformationGradient = multiply(targetCell, sourceInverse);
  if (!(determinant(deformationGradient) > 0)) return null;
  const rightCauchyGreen = multiply(transpose(deformationGradient), deformationGradient);
  const strain = rightCauchyGreen.map((row, first) => row.map((value, second) =>
    .5 * (value - Number(first === second))));
  const stressChange = subtract(targetStress, sourceStress);
  const parts = tensorParts(stressChange);
  return Object.freeze({ frameIndex, strain, stressChange,
    hydroStress: parts.hydro, deviatoricStress: parts.deviatoric,
    strainFrobenius: frobenius(strain), stressChangeFrobenius: frobenius(stressChange),
    deformationGradientDeterminant: determinant(deformationGradient) });
}

function fitCoefficients(records) {
  const hydroDenominator = records.reduce((sum, record) => sum + inner(record.hydroStress, record.hydroStress), 0);
  const deviatoricDenominator = records.reduce((sum, record) => sum + inner(record.deviatoricStress, record.deviatoricStress), 0);
  const hydroCompliance = hydroDenominator > 1e-14
    ? records.reduce((sum, record) => sum + inner(record.strain, record.hydroStress), 0) / hydroDenominator : null;
  const deviatoricCompliance = deviatoricDenominator > 1e-14
    ? records.reduce((sum, record) => sum + inner(record.strain, record.deviatoricStress), 0) / deviatoricDenominator : null;
  return { hydroCompliance, deviatoricCompliance, hydroDenominator, deviatoricDenominator };
}

function prediction(record, coefficients) {
  const hydroCompliance = coefficients.hydroCompliance
    ?? coefficients.hydroComplianceInverseGigaPascal;
  const deviatoricCompliance = coefficients.deviatoricCompliance
    ?? coefficients.deviatoricComplianceInverseGigaPascal;
  if (!Number.isFinite(hydroCompliance) || !Number.isFinite(deviatoricCompliance)) return null;
  return addScaled(record.hydroStress, record.deviatoricStress,
    deviatoricCompliance / hydroCompliance)
    .map((row) => row.map((value) => value * hydroCompliance));
}

export function fitArchivedStressStrainResponse(frames, options = {}) {
  const minimumRecords = Math.max(4, Number(options.minimumRecords) || 5);
  const maximumLinearStrain = Number.isFinite(Number(options.maximumLinearStrain))
    ? Math.max(.01, Math.min(.15, Number(options.maximumLinearStrain))) : .15;
  if (!Array.isArray(frames) || frames.length < minimumRecords + 1) {
    return Object.freeze({ available: false, promotionPassed: false, reason: `need at least ${minimumRecords + 1} paired frames` });
  }
  const referenceIndex = frames.length - 1;
  const reference = frames[referenceIndex];
  const allRecords = frames.slice(0, -1).map((frame, frameIndex) =>
    responseRecord(frame, reference, frameIndex)).filter(Boolean);
  const records = allRecords.filter((record) => record.strainFrobenius <= maximumLinearStrain);
  if (records.length < minimumRecords) {
    return Object.freeze({ available: false, promotionPassed: false,
      reason: `only ${records.length}/${minimumRecords} finite small-strain cell–stress pairs`,
      totalPairCount: allRecords.length, excludedNonlinearCount: allRecords.length - records.length,
      maximumLinearStrain });
  }
  const coefficients = fitCoefficients(records);
  if (!Number.isFinite(coefficients.hydroCompliance)
    || !Number.isFinite(coefficients.deviatoricCompliance)) {
    return Object.freeze({ available: false, promotionPassed: false,
      reason: "hydrostatic or deviatoric stress variation is rank deficient", records });
  }
  const loo = records.map((record, heldIndex) => {
    const trained = fitCoefficients(records.filter((_, index) => index !== heldIndex));
    const predicted = prediction(record, trained);
    const residual = predicted ? subtract(record.strain, predicted) : record.strain;
    return Object.freeze({ frameIndex: record.frameIndex, predicted,
      observedNorm: record.strainFrobenius,
      predictedNorm: predicted ? frobenius(predicted) : null,
      residualNorm: frobenius(residual) });
  });
  const zeroError = records.reduce((sum, record) => sum + inner(record.strain, record.strain), 0);
  const predictionError = loo.reduce((sum, row) => sum + row.residualNorm * row.residualNorm, 0);
  const crossValidatedSkill = zeroError > 1e-16 ? 1 - predictionError / zeroError : null;
  const sameSign = coefficients.hydroCompliance * coefficients.deviatoricCompliance > 0;
  const bulkModulusGigaPascal = 1 / (3 * Math.abs(coefficients.hydroCompliance));
  const shearModulusGigaPascal = 1 / (2 * Math.abs(coefficients.deviatoricCompliance));
  const maximumObservedStrain = Math.max(...records.map((record) => record.strainFrobenius));
  const promotionPassed = sameSign && Number.isFinite(crossValidatedSkill) && crossValidatedSkill >= .2
    && bulkModulusGigaPascal >= .1 && bulkModulusGigaPascal <= 2000
    && shearModulusGigaPascal >= .1 && shearModulusGigaPascal <= 2000
    && maximumObservedStrain <= .15;
  return Object.freeze({ available: true, promotionPassed,
    reason: promotionPassed ? "paired response passes fixed conditioning, sign, modulus, strain, and leave-one-frame-out gates"
      : "paired response remains descriptive; one or more fixed promotion gates failed",
    referenceIndex, recordCount: records.length, totalPairCount: allRecords.length,
    excludedNonlinearCount: allRecords.length - records.length, maximumLinearStrain,
    records: Object.freeze(records),
    hydroComplianceInverseGigaPascal: coefficients.hydroCompliance,
    deviatoricComplianceInverseGigaPascal: coefficients.deviatoricCompliance,
    inferredArchiveStressSign: coefficients.hydroCompliance >= 0 ? "tensile-positive" : "compressive-positive",
    complianceChannelsSameSign: sameSign,
    bulkModulusGigaPascal, shearModulusGigaPascal, maximumObservedStrain,
    crossValidatedSkill, leaveOneFrameOut: Object.freeze(loo),
    definition: "isotropic two-channel small-strain response fitted from archived stress change to final-cell Green–Lagrange strain",
    targetCoordinatesUsed: false, growthOutcomesUsed: false, physicalTimeUsed: false });
}

export function archivedResponseDeformationGradient(fit, frameIndex, maximumStrain = .04) {
  if (!fit?.promotionPassed || !(maximumStrain > 0) || maximumStrain > .1) return null;
  const record = fit.records?.find((entry) => entry.frameIndex === frameIndex);
  const predicted = record ? prediction(record, fit) : null;
  if (!predicted) return null;
  const norm = frobenius(predicted);
  const scale = norm > maximumStrain ? maximumStrain / norm : 1;
  const deformation = addScaled(identity3(), predicted, scale);
  return determinant(deformation) > .5 ? deformation : null;
}

const artifactNumber = (value, digits = 10) => Number.isFinite(value)
  ? Number(Number(value).toFixed(digits)) : null;

export function archivedStressStrainResponseArtifact(fit, options = {}) {
  if (!fit) return null;
  const selectedFrameIndex = Number.isInteger(options.selectedFrameIndex)
    ? options.selectedFrameIndex : 0;
  const selected = Boolean(options.selectedAsSoftRankingMetric);
  const magnitude = Number.isFinite(Number(options.maximumStrain))
    ? Number(options.maximumStrain) : .04;
  const selectedGradient = selected
    ? archivedResponseDeformationGradient(fit, selectedFrameIndex, magnitude) : null;
  return Object.freeze({
    available: Boolean(fit.available),
    promotionPassed: Boolean(fit.promotionPassed),
    reason: fit.reason || null,
    definition: fit.definition || null,
    referenceFrameIndexZeroBased: fit.referenceIndex ?? null,
    eligiblePairCount: fit.recordCount || 0,
    totalPairCount: fit.totalPairCount || 0,
    excludedNonlinearPairCount: fit.excludedNonlinearCount || 0,
    maximumLinearStrainFrobenius: fit.maximumLinearStrain ?? .15,
    hydroComplianceInverseGigaPascal: artifactNumber(fit.hydroComplianceInverseGigaPascal, 12),
    deviatoricComplianceInverseGigaPascal: artifactNumber(fit.deviatoricComplianceInverseGigaPascal, 12),
    inferredArchiveStressSign: fit.inferredArchiveStressSign || null,
    complianceChannelsSameSign: fit.complianceChannelsSameSign ?? null,
    apparentBulkResponseScaleGigaPascal: artifactNumber(fit.bulkModulusGigaPascal),
    apparentShearResponseScaleGigaPascal: artifactNumber(fit.shearModulusGigaPascal),
    maximumObservedStrainFrobenius: artifactNumber(fit.maximumObservedStrain),
    leaveOneFrameOutSkill: artifactNumber(fit.crossValidatedSkill),
    fitRecords: Object.freeze(fit.records?.map((record) => Object.freeze({
      frameIndexZeroBased: record.frameIndex,
      strainFrobenius: artifactNumber(record.strainFrobenius),
      stressChangeFrobeniusGigaPascal: artifactNumber(record.stressChangeFrobenius),
      deformationGradientDeterminant: artifactNumber(record.deformationGradientDeterminant),
    })) || []),
    leaveOneFrameOut: Object.freeze(fit.leaveOneFrameOut?.map((record) => Object.freeze({
      frameIndexZeroBased: record.frameIndex,
      observedStrainFrobenius: artifactNumber(record.observedNorm),
      predictedStrainFrobenius: artifactNumber(record.predictedNorm),
      residualStrainFrobenius: artifactNumber(record.residualNorm),
    })) || []),
    selectedFrameIndexZeroBased: selectedFrameIndex,
    selectedFrameEligible: Boolean(fit.records?.some((record) => record.frameIndex === selectedFrameIndex)),
    selectedDeformationGradient: selectedGradient
      ? Object.freeze(selectedGradient.map((row) => Object.freeze(row.map((value) => artifactNumber(value, 12)))))
      : null,
    selectedAsSoftRankingMetric: selected,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetCoordinatesUsed: false,
    growthOutcomesUsed: false,
    physicalTimeUsed: false,
    independentValidationClaimed: false,
    generalElasticTensorClaimed: false,
  });
}
