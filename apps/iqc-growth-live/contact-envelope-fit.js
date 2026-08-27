function finitePositive(value) {
  return Number.isFinite(value) && value > 0;
}

function solveLinearSystem(matrix, vector) {
  const size = vector.length;
  const rows = matrix.map((row, index) => [...row, vector[index]]);
  for (let column = 0; column < size; column++) {
    let pivot = column;
    for (let row = column + 1; row < size; row++) {
      if (Math.abs(rows[row][column]) > Math.abs(rows[pivot][column])) pivot = row;
    }
    if (Math.abs(rows[pivot][column]) < 1e-12) return null;
    [rows[column], rows[pivot]] = [rows[pivot], rows[column]];
    const divisor = rows[column][column];
    for (let entry = column; entry <= size; entry++) rows[column][entry] /= divisor;
    for (let row = 0; row < size; row++) {
      if (row === column) continue;
      const factor = rows[row][column];
      for (let entry = column; entry <= size; entry++) rows[row][entry] -= factor * rows[column][entry];
    }
  }
  return rows.map((row) => row[size]);
}

function matrixRank(rows, tolerance = 1e-10) {
  if (!rows.length) return 0;
  const work = rows.map((row) => [...row]);
  let rank = 0;
  for (let column = 0; column < work[0].length && rank < work.length; column++) {
    let pivot = rank;
    for (let row = rank + 1; row < work.length; row++) {
      if (Math.abs(work[row][column]) > Math.abs(work[pivot][column])) pivot = row;
    }
    if (Math.abs(work[pivot][column]) <= tolerance) continue;
    [work[rank], work[pivot]] = [work[pivot], work[rank]];
    for (let row = rank + 1; row < work.length; row++) {
      const factor = work[row][column] / work[rank][column];
      for (let entry = column; entry < work[row].length; entry++) work[row][entry] -= factor * work[rank][entry];
    }
    rank++;
  }
  return rank;
}

/**
 * Fit an additive species envelope r_i + r_j ~= d_ij to the leading observed
 * colored-contact shell. Cordero radii supply only a scale/ratio regularizer;
 * the returned values are sample-fitted geometric envelopes, not ionic,
 * metallic, van-der-Waals, oxidation-state, or force-field radii.
 */
export function fitAdditiveContactEnvelope(distanceModel, {
  priorRadiiAngstrom,
  sceneToAngstrom = 1,
  leadingShellRatio = 1.12,
  ridgeFraction = .08,
} = {}) {
  if (!distanceModel?.records?.length || !priorRadiiAngstrom || !finitePositive(sceneToAngstrom)
    || !finitePositive(leadingShellRatio) || leadingShellRatio < 1
    || !finitePositive(ridgeFraction)) return {
    available: false, reason: "colored contact records, positive units, and a radius prior are required",
    targetUsed: false,
  };
  const species = [...new Set(distanceModel.records.flatMap((record) => record.species))]
    .filter((symbol) => finitePositive(priorRadiiAngstrom[symbol])).sort();
  if (!species.length) return { available: false, reason: "no observed species has a finite radius prior", targetUsed: false };
  const speciesIndex = new Map(species.map((symbol, index) => [symbol, index]));
  const candidates = distanceModel.records.flatMap((record) => {
    const [first, second] = record.species || [];
    const priorSum = (priorRadiiAngstrom[first] || 0) + (priorRadiiAngstrom[second] || 0);
    const targetAngstrom = record.lowerContact * sceneToAngstrom;
    if (!speciesIndex.has(first) || !speciesIndex.has(second) || !finitePositive(priorSum)
      || !finitePositive(targetAngstrom)) return [];
    return [{ ...record, targetAngstrom, priorSum,
      priorNormalizedContact: targetAngstrom / priorSum,
      weight: Math.max(1, Math.log2(1 + (record.nearestObservations || 1))) }];
  }).sort((first, second) => first.priorNormalizedContact - second.priorNormalizedContact
    || first.key.localeCompare(second.key));
  if (!candidates.length) return { available: false, reason: "no finite colored contact can be fitted", targetUsed: false };
  const leadingThreshold = candidates[0].priorNormalizedContact * leadingShellRatio;
  const selected = candidates.filter((record) => record.priorNormalizedContact <= leadingThreshold + 1e-12);
  const excluded = candidates.filter((record) => !selected.includes(record));
  const priorScaleNumerator = selected.reduce((sum, record) => sum + record.weight * record.priorSum * record.targetAngstrom, 0);
  const priorScaleDenominator = selected.reduce((sum, record) => sum + record.weight * record.priorSum ** 2, 0);
  const priorScale = priorScaleNumerator / priorScaleDenominator;
  if (!finitePositive(priorScale)) return { available: false, reason: "the contact/prior scale is singular", targetUsed: false };
  const designRows = selected.map((record) => {
    const row = new Array(species.length).fill(0);
    row[speciesIndex.get(record.species[0])]++;
    row[speciesIndex.get(record.species[1])]++;
    return row;
  });
  const dataWeight = selected.reduce((sum, record) => sum + record.weight, 0);
  const ridgeWeight = ridgeFraction * dataWeight / species.length;
  const normal = Array.from({ length: species.length }, () => new Array(species.length).fill(0));
  const rhs = new Array(species.length).fill(0);
  selected.forEach((record, recordIndex) => {
    const row = designRows[recordIndex];
    row.forEach((firstValue, first) => {
      rhs[first] += record.weight * firstValue * record.targetAngstrom;
      row.forEach((secondValue, second) => { normal[first][second] += record.weight * firstValue * secondValue; });
    });
  });
  species.forEach((symbol, index) => {
    normal[index][index] += ridgeWeight;
    rhs[index] += ridgeWeight * priorScale * priorRadiiAngstrom[symbol];
  });
  const solution = solveLinearSystem(normal, rhs);
  if (!solution || solution.some((value) => !finitePositive(value))) return {
    available: false, reason: "the nonnegative additive contact fit is unresolved", targetUsed: false,
  };
  const radiiAngstrom = Object.fromEntries(species.map((symbol, index) => [symbol, solution[index]]));
  const radiiScene = Object.fromEntries(species.map((symbol) => [symbol, radiiAngstrom[symbol] / sceneToAngstrom]));
  const selectedPairs = selected.map((record) => {
    const predictedAngstrom = radiiAngstrom[record.species[0]] + radiiAngstrom[record.species[1]];
    return { key: record.key, species: [...record.species], targetAngstrom: record.targetAngstrom,
      predictedAngstrom, residualAngstrom: predictedAngstrom - record.targetAngstrom,
      nearestObservations: record.nearestObservations, weight: record.weight,
      priorNormalizedContact: record.priorNormalizedContact };
  });
  const squaredResidual = selectedPairs.reduce((sum, record) => sum + record.weight * record.residualAngstrom ** 2, 0);
  const rmsResidualAngstrom = Math.sqrt(squaredResidual / dataWeight);
  const maximumAbsoluteResidualAngstrom = Math.max(...selectedPairs.map((record) => Math.abs(record.residualAngstrom)));
  const supportedSpecies = new Set(selectedPairs.flatMap((record) => record.species));
  return {
    available: true,
    species,
    radiiAngstrom,
    radiiScene,
    selectedPairs,
    excludedPairs: excluded.map((record) => ({ key: record.key, species: [...record.species],
      targetAngstrom: record.targetAngstrom, priorNormalizedContact: record.priorNormalizedContact,
      nearestObservations: record.nearestObservations })),
    selectedPairCount: selectedPairs.length,
    excludedPairCount: excluded.length,
    selectedNearestObservations: selected.reduce((sum, record) => sum + (record.nearestObservations || 0), 0),
    supportedSpecies: [...supportedSpecies].sort(),
    unsupportedSpecies: species.filter((symbol) => !supportedSpecies.has(symbol)),
    supportedSpeciesFraction: supportedSpecies.size / species.length,
    dataRank: matrixRank(designRows),
    parameterCount: species.length,
    priorDependentParameterCount: Math.max(0, species.length - matrixRank(designRows)),
    priorScale,
    ridgeFraction,
    ridgeWeight,
    leadingShellRatio,
    leadingThreshold,
    rmsResidualAngstrom,
    maximumAbsoluteResidualAngstrom,
    rmsResidualRelativeToMeanContact: rmsResidualAngstrom
      / (selectedPairs.reduce((sum, record) => sum + record.targetAngstrom, 0) / selectedPairs.length),
    sceneToAngstrom,
    fitDefinition: "weighted additive species envelopes fitted to the leading observed colored-contact shell",
    priorDefinition: "Cordero covalent radii provide only a shared scale and ridge ratio prior",
    physicalRadiusIdentityInferred: false,
    oxidationStateOrCoordinationSpecificRadiusInferred: false,
    energyOrPotentialFitted: false,
    targetUsed: false,
    usedAsGrowthInput: false,
  };
}

