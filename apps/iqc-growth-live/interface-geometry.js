function vector(first, second) {
  return [second[0] - first[0], second[1] - first[1], second[2] - first[2]];
}

function dot(first, second) {
  return first[0] * second[0] + first[1] * second[1] + first[2] * second[2];
}

function norm(value) {
  return Math.hypot(...value);
}

function validatePoint(point, label) {
  if (!Array.isArray(point) || point.length !== 3 || !point.every(Number.isFinite)) {
    throw new Error(`${label} must be a finite Cartesian triple`);
  }
}

function connectedComponents(indices, positions, species, contactCutoff) {
  if (typeof contactCutoff !== "function") return null;
  const unseen = new Set(indices);
  let count = 0;
  while (unseen.size) {
    count++;
    const queue = [unseen.values().next().value];
    unseen.delete(queue[0]);
    while (queue.length) {
      const current = queue.shift();
      [...unseen].forEach((candidate) => {
        const cutoff = contactCutoff(species[current], species[candidate]);
        if (!Number.isFinite(cutoff) || cutoff <= 0) return;
        if (norm(vector(positions[current], positions[candidate])) > cutoff) return;
        unseen.delete(candidate); queue.push(candidate);
      });
    }
  }
  return count;
}

export function interfaceGeometryAudit({
  positions, species, memberships, firstNucleusId, secondNucleusId,
  firstCenter, secondCenter, lengthScale = 1, contactCutoff = null,
}) {
  if (!Array.isArray(positions) || !Array.isArray(species) || !Array.isArray(memberships)
    || positions.length !== species.length || positions.length !== memberships.length) {
    throw new Error("positions, species, and memberships must have equal lengths");
  }
  positions.forEach((point, index) => validatePoint(point, `positions[${index}]`));
  validatePoint(firstCenter, "firstCenter"); validatePoint(secondCenter, "secondCenter");
  if (!Number.isFinite(lengthScale) || lengthScale <= 0) throw new Error("lengthScale must be positive");
  const sharedIndices = memberships.map((ids, index) => Array.isArray(ids)
    && ids.includes(firstNucleusId) && ids.includes(secondNucleusId) ? index : null)
    .filter(Number.isInteger);
  const centerVector = vector(firstCenter, secondCenter);
  const centerSeparation = norm(centerVector);
  const axisDefined = centerSeparation > 1e-12;
  const axis = axisDefined ? centerVector.map((value) => value / centerSeparation) : [1, 0, 0];
  const midpoint = firstCenter.map((value, index) => .5 * (value + secondCenter[index]));
  const axial = sharedIndices.map((index) => dot(vector(midpoint, positions[index]), axis) * lengthScale);
  const axialMean = axial.length ? axial.reduce((sum, value) => sum + value, 0) / axial.length : null;
  const axialThickness = axial.length > 1
    ? Math.sqrt(axial.reduce((sum, value) => sum + (value - axialMean) ** 2, 0) / axial.length) : null;
  const axialSpan = axial.length > 1 ? Math.max(...axial) - Math.min(...axial) : null;
  const tangentialRadii = sharedIndices.map((index) => {
    const displacement = vector(midpoint, positions[index]);
    const projection = dot(displacement, axis);
    return Math.sqrt(Math.max(0, dot(displacement, displacement) - projection ** 2)) * lengthScale;
  });
  const tangentialRms = tangentialRadii.length
    ? Math.sqrt(tangentialRadii.reduce((sum, value) => sum + value ** 2, 0) / tangentialRadii.length) : null;
  const tangentialMaximum = tangentialRadii.length ? Math.max(...tangentialRadii) : null;
  const chemistry = Object.fromEntries([...new Set(sharedIndices.map((index) => species[index]))].sort()
    .map((symbol) => [symbol, sharedIndices.filter((index) => species[index] === symbol).length]));
  const componentCount = connectedComponents(sharedIndices, positions, species, contactCutoff);
  const profile = new Array(7).fill(0);
  if (axial.length) {
    const minimum = Math.min(...axial); const maximum = Math.max(...axial);
    axial.forEach((value) => {
      const bin = maximum - minimum <= 1e-12 ? 3
        : Math.min(6, Math.floor(7 * (value - minimum) / (maximum - minimum + 1e-12)));
      profile[bin]++;
    });
  }
  return {
    sharedIndices, sharedSiteCount: sharedIndices.length,
    axisDefined, centerSeparation: centerSeparation * lengthScale,
    axialCentroidOffset: axialMean, axialThicknessRms: axialThickness, axialSpan,
    tangentialRadiusRms: tangentialRms, tangentialRadiusMaximum: tangentialMaximum,
    componentCount, profile, chemistry,
    registryTopology: !sharedIndices.length ? "separated" : sharedIndices.length === 1
      ? "single registered site" : componentCount === 1 ? "connected registry patch"
        : componentCount === null ? "registry connectivity unresolved" : `${componentCount} registry patches`,
    finiteInterfaceGeometryResolved: axisDefined && sharedIndices.length >= 2,
    coordinateFrameUsed: false, targetUsed: false,
    physicalAreaInferred: false, interfacialEnergyInferred: false,
    interfaceMobilityInferred: false, physicalTimeIntegrated: false,
  };
}

export function interfaceAccommodationScore({
  newlyRegisteredSites, componentCount, properMisorientationDegrees, comparable,
}) {
  const supportScore = 1 - Math.exp(-Math.max(0, newlyRegisteredSites) / 2);
  const connectivityScore = Number.isInteger(componentCount) && componentCount > 0
    ? Math.max(-1, Math.min(1, 2 / componentCount - 1)) : 0;
  const orientationScore = comparable && Number.isFinite(properMisorientationDegrees)
    ? Math.max(-1, Math.min(1, 1 - 2 * properMisorientationDegrees / 180)) : 0;
  const score = Math.max(-1, Math.min(1,
    .4 * supportScore + .35 * connectivityScore + .25 * orientationScore));
  return { score, supportScore, connectivityScore, orientationScore,
    formula: "0.40 registered-support + 0.35 colored-contact connectivity + 0.25 proper-misorientation compatibility" };
}
