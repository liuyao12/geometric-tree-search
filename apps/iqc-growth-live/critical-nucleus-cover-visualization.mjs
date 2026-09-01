function finiteVector(value, label) {
  if (!Array.isArray(value) || value.length !== 3
      || value.some(entry => !Number.isFinite(Number(entry)))) {
    throw new TypeError(`${label} must be a finite 3-vector`);
  }
  return value.map(Number);
}

function cross(first, second, third) {
  return (second.x - first.x) * (third.y - first.y)
    - (second.y - first.y) * (third.x - first.x);
}

function convexHull(points) {
  if (points.length <= 2) return points.map(point => point.siteIndex);
  const sorted = points.slice().sort((first, second) => first.x - second.x
    || first.y - second.y || first.siteIndex - second.siteIndex);
  const lower = [];
  for (const point of sorted) {
    while (lower.length >= 2 && cross(lower.at(-2), lower.at(-1), point) <= 1e-10) lower.pop();
    lower.push(point);
  }
  const upper = [];
  for (const point of sorted.slice().reverse()) {
    while (upper.length >= 2 && cross(upper.at(-2), upper.at(-1), point) <= 1e-10) upper.pop();
    upper.push(point);
  }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)].map(point => point.siteIndex);
}

function typeHue(typeId) {
  return (Number(typeId) * 137.508 + 188) % 360;
}

export function buildCriticalNucleusCoverVisualization(geometry, posedEvent, admission, options = {}) {
  if (geometry?.schema !== "gcts-critical-nucleus-geometry-evidence-v1"
      || geometry.targetUsed || admission?.targetUsed || admission?.candidateSetInspected) {
    throw new Error("target-blind geometry and grammar admission are required");
  }
  const width = Number(options.width ?? 320); const height = Number(options.height ?? 136);
  const padding = Number(options.padding ?? 18); const captionHeight = Number(options.captionHeight ?? 18);
  if (!(width > 2 * padding) || !(height > 2 * padding + captionHeight)) {
    throw new RangeError("visualization dimensions leave no plot area");
  }
  const sourceSites = posedEvent?.sites || geometry.sites;
  if (!Array.isArray(sourceSites) || sourceSites.length !== geometry.sites.length) {
    throw new Error("posed event must preserve every supplied nucleus site");
  }
  const positions = sourceSites.map((site, index) => finiteVector(
    site.localRotatedPositionAngstrom || site.positionAngstrom,
    `site ${index} position`,
  ));
  const xCenter = positions.reduce((sum, point) => sum + point[0], 0) / Math.max(1, positions.length);
  const yCenter = positions.reduce((sum, point) => sum + point[1], 0) / Math.max(1, positions.length);
  const extent = Math.max(1e-9, ...positions.map(point => Math.hypot(point[0] - xCenter,
    point[1] - yCenter)));
  const radius = Math.min(width / 2 - padding, (height - captionHeight) / 2 - padding);
  const projected = positions.map((point, siteIndex) => ({
    siteIndex,
    x: width / 2 + (point[0] - xCenter) / extent * radius,
    y: (height - captionHeight) / 2 - (point[1] - yCenter) / extent * radius,
    z: point[2],
  }));
  const ownership = projected.map(() => []);
  const occurrences = (admission?.selectedOccurrences || []).map((occurrence, occurrenceIndex) => {
    const support = [...new Set(occurrence.supportSiteIndices || [])].sort((a, b) => a - b);
    if (!support.length || support.some(index => !Number.isInteger(index)
        || index < 0 || index >= projected.length)) throw new Error("occurrence support is invalid");
    support.forEach(index => ownership[index].push(occurrence.typeId));
    const points = support.map(index => projected[index]);
    const centroid = points.reduce((sum, point) => ({ x: sum.x + point.x, y: sum.y + point.y }),
      { x: 0, y: 0 });
    centroid.x /= points.length; centroid.y /= points.length;
    return {
      occurrenceId: occurrence.occurrenceId,
      occurrenceIndex,
      typeId: occurrence.typeId,
      supportSiteIndices: support,
      hullSiteIndices: convexHull(points),
      centroid,
      radiusPixels: Math.max(4, ...points.map(point => Math.hypot(point.x - centroid.x,
        point.y - centroid.y))),
      frontier: occurrence.outgoingRuleCount > 0,
      outgoingRuleCount: occurrence.outgoingRuleCount,
      hue: typeHue(occurrence.typeId),
    };
  });
  const occurrenceById = new Map(occurrences.map(occurrence => [occurrence.occurrenceId, occurrence]));
  const edges = (admission?.admittedConnectionEdges || []).map(edge => {
    const first = occurrenceById.get(edge.firstOccurrenceId);
    const second = occurrenceById.get(edge.secondOccurrenceId);
    if (!first || !second) throw new Error("admitted edge references an unknown selected occurrence");
    return { ...edge, first: { ...first.centroid }, second: { ...second.centroid } };
  });
  const residualSet = new Set((admission?.residualSites || []).map(site => site.siteIndex));
  const atoms = geometry.sites.map((site, siteIndex) => ({
    siteIndex, siteId: site.siteId, species: site.species, region: site.region,
    membershipProbability: site.membershipProbability,
    ...projected[siteIndex], typeIds: [...new Set(ownership[siteIndex])].sort((a, b) => a - b),
    recognized: ownership[siteIndex].length > 0,
    residual: residualSet.has(siteIndex),
  }));
  if (atoms.some(atom => atom.recognized === atom.residual)) {
    throw new Error("recognized and residual atom partition is inconsistent");
  }
  return {
    schema: "gcts-critical-nucleus-cover-visualization-v1",
    width, height, captionHeight, atoms, occurrences, edges,
    recognizedAtomCount: atoms.filter(atom => atom.recognized).length,
    residualAtomCount: atoms.filter(atom => atom.residual).length,
    frontierOccurrenceCount: occurrences.filter(occurrence => occurrence.frontier).length,
    targetUsed: false,
    candidateSetChanged: false,
  };
}
