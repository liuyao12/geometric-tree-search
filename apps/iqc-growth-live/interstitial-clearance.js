import { directionalDisplacementSupport, displacementClearanceKey,
  DISPLACEMENT_SIGMA_MULTIPLIERS, normalizeDisplacementTensors }
  from "./displacement-envelope.js?v=20260827-1";

function squaredDistance(first, second) {
  let total = 0;
  for (let axis = 0; axis < first.length; axis++) {
    const delta = first[axis] - second[axis]; total += delta * delta;
  }
  return total;
}

function quantile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((first, second) => first - second);
  const position = Math.max(0, Math.min(sorted.length - 1, fraction * (sorted.length - 1)));
  const lower = Math.floor(position); const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function centroid(positions) {
  const center = new Array(positions[0]?.length || 3).fill(0);
  positions.forEach((point) => point.forEach((value, axis) => { center[axis] += value / positions.length; }));
  return center;
}

function determinant3(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

function solveLinear(matrix, values) {
  if (matrix.length === 2) {
    const determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    if (Math.abs(determinant) < 1e-11) return null;
    return [(values[0] * matrix[1][1] - matrix[0][1] * values[1]) / determinant,
      (matrix[0][0] * values[1] - values[0] * matrix[1][0]) / determinant];
  }
  const determinant = determinant3(matrix);
  if (Math.abs(determinant) < 1e-11) return null;
  return [0, 1, 2].map((column) => {
    const replaced = matrix.map((row, rowIndex) => row.map((value, columnIndex) =>
      columnIndex === column ? values[rowIndex] : value));
    return determinant3(replaced) / determinant;
  });
}

function combinations(values, size, start = 0, prefix = [], result = []) {
  if (prefix.length === size) { result.push(prefix); return result; }
  for (let index = start; index <= values.length - (size - prefix.length); index++) {
    combinations(values, size, index + 1, [...prefix, values[index]], result);
  }
  return result;
}

function canonicalAnchors(positions, maximumAnchors) {
  if (positions.length <= maximumAnchors) return positions.map((_, index) => index);
  const center = centroid(positions);
  const records = positions.map((point, index) => ({ index, radius2: squaredDistance(point, center),
    fingerprint: positions.map((other, otherIndex) => otherIndex === index ? 0 : squaredDistance(point, other))
      .sort((first, second) => first - second) }));
  const maximumRadius2 = Math.max(1e-18, ...records.map((record) => record.radius2));
  const maximumDistance2 = Math.max(1e-18, ...records.map((record) => record.fingerprint.at(-1)));
  records.forEach((record) => { record.canonicalKey = [Math.round(record.radius2 / maximumRadius2 * 1e10),
    ...record.fingerprint.map((value) => Math.round(value / maximumDistance2 * 1e10))]; });
  records.sort((first, second) => {
    for (let index = 0; index < first.canonicalKey.length; index++) {
      if (first.canonicalKey[index] !== second.canonicalKey[index]) {
        return first.canonicalKey[index] - second.canonicalKey[index];
      }
    }
    return 0;
  });
  const keyText = (record) => record.canonicalKey.join(",");
  const selectedKeys = new Set(Array.from({ length: maximumAnchors }, (_, sample) => keyText(records[
    Math.min(records.length - 1, Math.floor((sample + .5) * records.length / maximumAnchors))])));
  return records.filter((record) => selectedKeys.has(keyText(record))).map((record) => record.index);
}

function referenceNearestNeighborScale(positions, maximumAnchors) {
  const distances = canonicalAnchors(positions, maximumAnchors).map((index) => Math.sqrt(Math.min(
    ...positions.map((point, other) => other === index ? Infinity : squaredDistance(positions[index], point)))));
  return quantile(distances.filter(Number.isFinite), .5);
}

function simplexCircumcenter(vertices, requireInterior = true) {
  const origin = vertices[0];
  const edges = vertices.slice(1).map((point) => point.map((value, axis) => value - origin[axis]));
  const gram = edges.map((first) => edges.map((second) => first.reduce((sum, value, axis) => sum + value * second[axis], 0)));
  const weights = solveLinear(gram, edges.map((edge) => squaredDistance(edge, new Array(edge.length).fill(0)) / 2));
  if (!weights) return null;
  const offset = origin.map((_, axis) => edges.reduce((sum, edge, index) => sum + weights[index] * edge[axis], 0));
  const center = origin.map((value, axis) => value + offset[axis]);
  const barycentric = [1 - weights.reduce((sum, value) => sum + value, 0), ...weights];
  if (requireInterior && barycentric.some((weight) => weight < -1e-8 || weight > 1 + 1e-8)) return null;
  return center;
}

function witnessedEmptyCenters(positions, dimension, maximumAnchors, neighborLimit,
  anchorIndices = null, requireInterior = true) {
  const candidates = [];
  (anchorIndices || canonicalAnchors(positions, maximumAnchors)).forEach((anchor) => {
    const ordered = positions.map((point, index) => ({ index, distance2: index === anchor
      ? Infinity : squaredDistance(positions[anchor], point) })).sort((first, second) => first.distance2 - second.distance2);
    const finite = ordered.filter((record) => Number.isFinite(record.distance2));
    const cutoff = finite[Math.min(neighborLimit - 1, finite.length - 1)]?.distance2 ?? Infinity;
    const neighbors = finite.filter((record) => record.distance2 <= cutoff * (1 + 1e-10) + 1e-12)
      .map((record) => record.index);
    combinations(neighbors, dimension).forEach((others) => {
      const vertices = [anchor, ...others];
      const center = simplexCircumcenter(vertices.map((index) => positions[index]), requireInterior);
      if (!center) return;
      const radius2 = squaredDistance(center, positions[anchor]);
      const minimumDistance2 = Math.min(...positions.map((point) => squaredDistance(center, point)));
      if (minimumDistance2 + 1e-9 < radius2) return;
      candidates.push({ center, clearance: Math.sqrt(minimumDistance2), vertices: [...vertices].sort((a, b) => a - b) });
    });
  });
  const parents = candidates.map((_, index) => index);
  const root = (index) => { while (parents[index] !== index) { parents[index] = parents[parents[index]]; index = parents[index]; } return index; };
  const unite = (first, second) => { const a = root(first); const b = root(second); if (a !== b) parents[Math.max(a, b)] = Math.min(a, b); };
  const tolerance = 1e-6;
  const neighborOffsets = [];
  const buildOffsets = (prefix = []) => {
    if (prefix.length === dimension) { neighborOffsets.push(prefix); return; }
    [-1, 0, 1].forEach((value) => buildOffsets([...prefix, value]));
  };
  buildOffsets();
  const cells = new Map();
  candidates.forEach((candidate, index) => {
    const cell = candidate.center.map((value) => Math.floor(value / tolerance));
    neighborOffsets.forEach((offset) => {
      const key = cell.map((value, axis) => value + offset[axis]).join(",");
      (cells.get(key) || []).forEach((other) => {
        if (squaredDistance(candidate.center, candidates[other].center) <= tolerance * tolerance) unite(index, other);
      });
    });
    const key = cell.join(","); if (!cells.has(key)) cells.set(key, []); cells.get(key).push(index);
  });
  const components = new Map();
  candidates.forEach((candidate, index) => {
    const key = root(index); if (!components.has(key)) components.set(key, []); components.get(key).push(candidate);
  });
  return [...components.values()].map((records) => ({
    center: records[0].center.map((_, axis) => records.reduce((sum, record) => sum + record.center[axis], 0) / records.length),
    clearance: records.reduce((sum, record) => sum + record.clearance, 0) / records.length,
    simplices: records.map((record) => record.vertices),
  })).sort((first, second) => first.clearance - second.clearance);
}

function pointMinimumSiteClearance(center, positions, frameworkRadii = null,
  displacementTensors = null, sigmaMultiplier = 0) {
  return Math.min(...positions.map((point, index) => {
    const direction = center.map((value, axis) => value - point[axis]);
    return Math.sqrt(squaredDistance(center, point)) - (frameworkRadii?.[index] || 0)
      - directionalDisplacementSupport(displacementTensors?.[index], direction, sigmaMultiplier);
  }));
}

function segmentMinimumSiteClearance(first, second, positions, frameworkRadii = null,
  displacementTensors = null, sigmaMultiplier = 0) {
  const direction = second.map((value, axis) => value - first[axis]);
  const length2 = direction.reduce((sum, value) => sum + value * value, 0);
  if (length2 <= 1e-20) return pointMinimumSiteClearance(first, positions, frameworkRadii,
    displacementTensors, sigmaMultiplier);
  let minimum = Infinity;
  positions.forEach((point, index) => {
    const projection = point.reduce((sum, value, axis) => sum + (value - first[axis]) * direction[axis], 0) / length2;
    const parameter = Math.max(0, Math.min(1, projection));
    const closest = first.map((value, axis) => value + parameter * direction[axis]);
    const siteToClosest = closest.map((value, axis) => value - point[axis]);
    minimum = Math.min(minimum, Math.sqrt(squaredDistance(point, closest)) - (frameworkRadii?.[index] || 0)
      - directionalDisplacementSupport(displacementTensors?.[index], siteToClosest, sigmaMultiplier));
  });
  return minimum;
}

function clearanceModelsAtPoint(center, positions, covalentRadii, fittedRadii, displacementTensors) {
  const models = { point: null, covalent: covalentRadii, fitted: fittedRadii };
  return Object.fromEntries(Object.entries(models).flatMap(([model, radii]) => [0, ...DISPLACEMENT_SIGMA_MULTIPLIERS]
    .map((sigma) => [displacementClearanceKey(model, sigma),
      pointMinimumSiteClearance(center, positions, radii, displacementTensors, sigma)])));
}

function clearanceModelsAlongSegment(first, second, positions, covalentRadii, fittedRadii, displacementTensors) {
  const models = { point: null, covalent: covalentRadii, fitted: fittedRadii };
  return Object.fromEntries(Object.entries(models).flatMap(([model, radii]) => [0, ...DISPLACEMENT_SIGMA_MULTIPLIERS]
    .map((sigma) => [displacementClearanceKey(model, sigma),
      segmentMinimumSiteClearance(first, second, positions, radii, displacementTensors, sigma)])));
}

function imageOffsets(periodicAxes, radius = 1) {
  const offsets = [];
  const build = (prefix = []) => {
    if (prefix.length === 3) { offsets.push(prefix); return; }
    const axis = prefix.length;
    if (!periodicAxes[axis]) { build([...prefix, 0]); return; }
    for (let value = -radius; value <= radius; value++) build([...prefix, value]);
  };
  build();
  return offsets.sort((first, second) => first.reduce((sum, value) => sum + Math.abs(value), 0)
    - second.reduce((sum, value) => sum + Math.abs(value), 0)
    || first.join(",").localeCompare(second.join(",")));
}

function translatedPoint(point, cellVectors, image) {
  return point.map((value, axis) => value + cellVectors.reduce((sum, vector, cellAxis) =>
    sum + vector[axis] * image[cellAxis], 0));
}

function fractionalCoordinate(point, cellVectors) {
  return solveLinear(point.map((_, axis) => cellVectors.map((vector) => vector[axis])), point);
}

function vectorRank(vectors) {
  const basis = [];
  vectors.forEach((vector) => {
    const reduced = [...vector];
    basis.forEach((entry) => {
      const denominator = entry.reduce((sum, value) => sum + value * value, 0);
      const projection = reduced.reduce((sum, value, axis) => sum + value * entry[axis], 0) / denominator;
      entry.forEach((value, axis) => { reduced[axis] -= projection * value; });
    });
    if (Math.sqrt(reduced.reduce((sum, value) => sum + value * value, 0)) > 1e-8) basis.push(reduced);
  });
  return basis.length;
}

function periodicGraphAudit(nodeCount, edges, admittedNodes = null, admittedEdges = null) {
  const nodes = admittedNodes || new Set(Array.from({ length: nodeCount }, (_, index) => index));
  const selectedEdges = admittedEdges || edges.filter((edge) => nodes.has(edge.first) && nodes.has(edge.second));
  const adjacency = Array.from({ length: nodeCount }, () => []);
  selectedEdges.forEach((edge) => {
    adjacency[edge.first].push({ node: edge.second, shift: edge.imageShift });
    adjacency[edge.second].push({ node: edge.first, shift: edge.imageShift.map((value) => -value) });
  });
  const visited = new Set();
  const components = [];
  nodes.forEach((start) => {
    if (visited.has(start)) return;
    const queue = [start];
    const potentials = new Map([[start, [0, 0, 0]]]);
    const componentNodes = [];
    const windingVectors = [];
    visited.add(start);
    while (queue.length) {
      const node = queue.shift();
      componentNodes.push(node);
      adjacency[node].forEach((neighbor) => {
        const expected = potentials.get(node).map((value, axis) => value + neighbor.shift[axis]);
        if (!potentials.has(neighbor.node)) {
          potentials.set(neighbor.node, expected); visited.add(neighbor.node); queue.push(neighbor.node);
        } else {
          const winding = expected.map((value, axis) => value - potentials.get(neighbor.node)[axis]);
          if (winding.some((value) => value !== 0)) windingVectors.push(winding);
        }
      });
    }
    const uniqueWinding = [...new Map(windingVectors.map((vector) => {
      const sign = vector.find((value) => value !== 0) < 0 ? -1 : 1;
      const canonical = vector.map((value) => value * sign);
      return [canonical.join(","), canonical];
    })).values()].sort((first, second) => first.join(",").localeCompare(second.join(",")));
    components.push({ nodes: componentNodes.sort((a, b) => a - b), nodeCount: componentNodes.length,
      windingVectors: uniqueWinding, windingRank: vectorRank(uniqueWinding),
      percolatingAxes: [0, 1, 2].filter((axis) => uniqueWinding.some((vector) => vector[axis] !== 0)) });
  });
  components.sort((first, second) => second.nodeCount - first.nodeCount || second.windingRank - first.windingRank);
  const windingVectors = [...new Map(components.flatMap((component) => component.windingVectors)
    .map((vector) => [vector.join(","), vector])).values()];
  return { componentCount: components.length, largestComponentNodes: components[0]?.nodeCount || 0,
    windingVectors, windingRank: vectorRank(windingVectors),
    percolatingAxes: [0, 1, 2].filter((axis) => windingVectors.some((vector) => vector[axis] !== 0)), components };
}

function periodicWitnessedSummary(positions, dimension, maximumAnchors, neighborLimit,
  declaredThreshold, frameworkRadii, fittedFrameworkRadii, displacementTensors, cellVectors, periodicAxes) {
  if (dimension !== 3 || cellVectors?.length !== 3 || !periodicAxes?.some(Boolean)) return null;
  const determinant = determinant3(cellVectors.map((_, axis) => cellVectors.map((vector) => vector[axis])));
  if (Math.abs(determinant) < 1e-10) return null;
  const offsets = imageOffsets(periodicAxes);
  const extended = [];
  offsets.forEach((image) => positions.forEach((point, site) => extended.push({
    point: translatedPoint(point, cellVectors, image), site, image,
    radius: frameworkRadii?.[site] || 0,
    fittedRadius: fittedFrameworkRadii?.[site] || 0,
    displacementTensor: displacementTensors?.[site] || null,
  })));
  const extendedPositions = extended.map((record) => record.point);
  const anchors = canonicalAnchors(positions, maximumAnchors);
  const rawCenters = witnessedEmptyCenters(extendedPositions, dimension, maximumAnchors, neighborLimit, anchors, false);
  const centerFraction = fractionalCoordinate(centroid(positions), cellVectors);
  const quotient = new Map();
  rawCenters.forEach((record) => {
    const fractional = fractionalCoordinate(record.center, cellVectors);
    const image = fractional.map((value, axis) => periodicAxes[axis]
      ? Math.floor(value - centerFraction[axis] + .5) : 0);
    const center = translatedPoint(record.center, cellVectors, image.map((value) => -value));
    const key = center.map((value) => Math.round(value * 1e6)).join(",");
    if (!quotient.has(key)) quotient.set(key, { center, clearances: [], simplices: [] });
    const target = quotient.get(key);
    target.clearances.push(record.clearance);
    record.simplices.forEach((simplex) => target.simplices.push(simplex.map((extendedIndex) => ({
      site: extended[extendedIndex].site,
      image: extended[extendedIndex].image.map((value, axis) => value - image[axis]),
    }))));
  });
  const centers = [...quotient.values()].map((record) => ({ center: record.center,
    clearance: record.clearances.reduce((sum, value) => sum + value, 0) / record.clearances.length,
    simplices: [...new Map(record.simplices.map((simplex) => [simplex.map((site) =>
      `${site.site}@${site.image.join(",")}`).sort().join("|"), simplex])).values()] }))
    .sort((first, second) => first.center.join(",").localeCompare(second.center.join(",")));
  const structureCenter = centroid(positions);
  const maximumStructureRadius = Math.max(1e-12, ...centers.map((record) =>
    Math.sqrt(squaredDistance(record.center, structureCenter))));
  const extendedCovalentRadii = extended.map((record) => record.radius);
  const extendedFittedRadii = extended.map((record) => record.fittedRadius);
  const extendedDisplacementTensors = extended.map((record) => record.displacementTensor);
  const records = centers.map((record) => ({ clearance: record.clearance,
    stericClearance: frameworkRadii ? Math.min(...extended.map((site) =>
      Math.sqrt(squaredDistance(record.center, site.point)) - site.radius)) : null,
    fittedStericClearance: fittedFrameworkRadii ? Math.min(...extended.map((site) =>
      Math.sqrt(squaredDistance(record.center, site.point)) - site.fittedRadius)) : null,
    clearanceModels: clearanceModelsAtPoint(record.center, extendedPositions, frameworkRadii
      ? extendedCovalentRadii : null, fittedFrameworkRadii ? extendedFittedRadii : null,
    extendedDisplacementTensors),
    normalizedRadius: Math.sqrt(squaredDistance(record.center, structureCenter)) / maximumStructureRadius }));
  const faceBuckets = new Map();
  centers.forEach((center, centerIndex) => center.simplices.forEach((simplex) =>
    combinations(simplex, dimension).forEach((face) => offsets.forEach((shift) => {
      const faceKey = face.map((record) => `${record.site}@${record.image
        .map((value, axis) => value + shift[axis]).join(",")}`).sort().join("|");
      if (!faceBuckets.has(faceKey)) faceBuckets.set(faceKey, new Map());
      faceBuckets.get(faceKey).set(`${centerIndex}:${shift.join(",")}`,
        { center: centerIndex, shift: [...shift] });
    }))));
  const edgeMap = new Map();
  faceBuckets.forEach((bucket) => {
    const witnesses = [...bucket.values()];
    for (let firstWitness = 0; firstWitness < witnesses.length; firstWitness++) {
      for (let secondWitness = firstWitness + 1; secondWitness < witnesses.length; secondWitness++) {
        let first = witnesses[firstWitness].center;
        let second = witnesses[secondWitness].center;
        let imageShift = witnesses[secondWitness].shift.map((value, axis) =>
          value - witnesses[firstWitness].shift[axis]);
        if (first > second) {
          [first, second] = [second, first]; imageShift = imageShift.map((value) => -value);
        }
        if (first === second && imageShift.every((value) => value === 0)) continue;
        if (first === second && imageShift.find((value) => value !== 0) < 0) imageShift = imageShift.map((value) => -value);
        const key = `${first}:${second}:${imageShift.join(",")}`;
        if (edgeMap.has(key)) continue;
      const secondCenter = translatedPoint(centers[second].center, cellVectors, imageShift);
      const throatClearance = segmentMinimumSiteClearance(centers[first].center, secondCenter, extendedPositions);
      const stericThroatClearance = frameworkRadii ? segmentMinimumSiteClearance(centers[first].center,
        secondCenter, extendedPositions, extended.map((record) => record.radius)) : null;
      const fittedStericThroatClearance = fittedFrameworkRadii ? segmentMinimumSiteClearance(centers[first].center,
        secondCenter, extendedPositions, extended.map((record) => record.fittedRadius)) : null;
      const clearanceModels = clearanceModelsAlongSegment(centers[first].center, secondCenter, extendedPositions,
        frameworkRadii ? extendedCovalentRadii : null, fittedFrameworkRadii ? extendedFittedRadii : null,
        extendedDisplacementTensors);
        edgeMap.set(key, { first, second, imageShift: [...imageShift], sharedSiteCount: dimension,
        throatClearance, stericThroatClearance, fittedStericThroatClearance, clearanceModels,
        throatToEndpointRatio: Math.max(0, Math.min(1, throatClearance
          / Math.max(1e-12, Math.min(records[first].clearance, records[second].clearance)))) });
      }
    }
  });
  const edges = [...edgeMap.values()];
  const pointAudit = (threshold) => periodicGraphAudit(centers.length, edges,
    new Set(records.map((record, index) => record.clearance >= threshold ? index : -1).filter((index) => index >= 0)),
    edges.filter((edge) => edge.throatClearance >= threshold
      && records[edge.first].clearance >= threshold && records[edge.second].clearance >= threshold));
  const stericAudit = (threshold) => periodicGraphAudit(centers.length, edges,
    new Set(records.map((record, index) => record.stericClearance >= threshold ? index : -1).filter((index) => index >= 0)),
    edges.filter((edge) => edge.stericThroatClearance >= threshold
      && records[edge.first].stericClearance >= threshold && records[edge.second].stericClearance >= threshold));
  const fittedStericAudit = (threshold) => periodicGraphAudit(centers.length, edges,
    new Set(records.map((record, index) => record.fittedStericClearance >= threshold ? index : -1).filter((index) => index >= 0)),
    edges.filter((edge) => edge.fittedStericThroatClearance >= threshold
      && records[edge.first].fittedStericClearance >= threshold
      && records[edge.second].fittedStericClearance >= threshold));
  const full = periodicGraphAudit(centers.length, edges);
  const threshold = pointAudit(declaredThreshold);
  const capacities = [...new Set([...records.map((record) => record.clearance),
    ...edges.map((edge) => edge.throatClearance)])].sort((first, second) => second - first);
  const stericCapacities = frameworkRadii ? [...new Set([...records.map((record) => record.stericClearance),
    ...edges.map((edge) => edge.stericThroatClearance)])].sort((first, second) => second - first) : [];
  const fittedStericCapacities = fittedFrameworkRadii ? [...new Set([...records.map((record) => record.fittedStericClearance),
    ...edges.map((edge) => edge.fittedStericThroatClearance)])].sort((first, second) => second - first) : [];
  const widest = capacities.find((value) => pointAudit(value).windingRank > 0) ?? null;
  const widestSteric = stericCapacities.find((value) => stericAudit(value).windingRank > 0) ?? null;
  const widestFittedSteric = fittedStericCapacities.find((value) => fittedStericAudit(value).windingRank > 0) ?? null;
  return { candidateCenters: centers.length, radialRecords: records,
    medianClearance: quantile(records.map((record) => record.clearance), .5),
    percentile90Clearance: quantile(records.map((record) => record.clearance), .9),
    maximumClearance: records.length ? Math.max(...records.map((record) => record.clearance)) : null,
    network: { nodeCount: centers.length, edgeCount: edges.length,
      wrappedEdgeCount: edges.filter((edge) => edge.imageShift.some((value) => value !== 0)).length,
      periodicAxes: [...periodicAxes], edges, ...full,
      thresholdNodeCount: records.filter((record) => record.clearance >= declaredThreshold).length,
      thresholdEdgeCount: edges.filter((edge) => edge.throatClearance >= declaredThreshold
        && records[edge.first].clearance >= declaredThreshold && records[edge.second].clearance >= declaredThreshold).length,
      thresholdComponentCount: threshold.componentCount,
      thresholdLargestComponentNodes: threshold.largestComponentNodes,
      thresholdWindingRank: threshold.windingRank,
      thresholdPercolatingAxes: threshold.percolatingAxes,
      widestPeriodicClearance: widest,
      widestStericPeriodicClearance: widestSteric,
      widestFittedStericPeriodicClearance: widestFittedSteric,
      minimumThroatClearance: edges.length ? Math.min(...edges.map((edge) => edge.throatClearance)) : null,
      medianThroatClearance: quantile(edges.map((edge) => edge.throatClearance), .5),
      medianStericThroatClearance: frameworkRadii
        ? quantile(edges.map((edge) => edge.stericThroatClearance), .5) : null,
      medianFittedStericThroatClearance: fittedFrameworkRadii
        ? quantile(edges.map((edge) => edge.fittedStericThroatClearance), .5) : null,
      adjacencyDefinition: "two quotient empty centers are adjacent only when lifted witnessed tetrahedra share a complete three-site face",
      windingDefinition: "nonzero integer cell translation accumulated around a closed lifted-graph cycle",
    },
    periodicQuotient: true, imageRange: 1, targetUsed: false };
}

function emptyCenterNetwork(centers, radialRecords, dimension, positions, declaredThreshold,
  frameworkRadii, fittedFrameworkRadii, displacementTensors) {
  const edges = [];
  for (let first = 0; first < centers.length; first++) for (let second = first + 1; second < centers.length; second++) {
    let sharedSiteCount = 0;
    centers[first].simplices.some((firstSimplex) => centers[second].simplices.some((secondSimplex) => {
      const shared = firstSimplex.filter((site) => secondSimplex.includes(site)).length;
      sharedSiteCount = Math.max(sharedSiteCount, shared); return shared >= dimension;
    }));
    if (sharedSiteCount >= dimension) {
      const throatClearance = segmentMinimumSiteClearance(centers[first].center, centers[second].center, positions);
      const stericThroatClearance = frameworkRadii
        ? segmentMinimumSiteClearance(centers[first].center, centers[second].center, positions, frameworkRadii) : null;
      const fittedStericThroatClearance = fittedFrameworkRadii
        ? segmentMinimumSiteClearance(centers[first].center, centers[second].center, positions, fittedFrameworkRadii) : null;
      const clearanceModels = clearanceModelsAlongSegment(centers[first].center, centers[second].center, positions,
        frameworkRadii, fittedFrameworkRadii, displacementTensors);
      const endpointClearance = Math.min(radialRecords[first].clearance, radialRecords[second].clearance);
      edges.push({ first, second, sharedSiteCount, throatClearance, stericThroatClearance, fittedStericThroatClearance,
        clearanceModels,
        throatToEndpointRatio: Math.max(0, Math.min(1, throatClearance / Math.max(1e-12, endpointClearance))) });
    }
  }
  const parents = centers.map((_, index) => index);
  const root = (index) => { while (parents[index] !== index) { parents[index] = parents[parents[index]]; index = parents[index]; } return index; };
  const unite = (first, second) => { const a = root(first); const b = root(second); if (a !== b) parents[Math.max(a, b)] = Math.min(a, b); };
  edges.forEach((edge) => unite(edge.first, edge.second));
  const components = new Map();
  centers.forEach((_, index) => { const key = root(index); if (!components.has(key)) components.set(key, []); components.get(key).push(index); });
  const componentRecords = [...components.values()].map((nodes, component) => {
    const radii = nodes.map((node) => radialRecords[node].normalizedRadius);
    const nodeSet = new Set(nodes);
    const edgeCount = edges.filter((edge) => nodeSet.has(edge.first) && nodeSet.has(edge.second)).length;
    return { component, nodes, nodeCount: nodes.length, edgeCount,
      cycleRank: Math.max(0, edgeCount - nodes.length + 1),
      minimumNormalizedRadius: Math.min(...radii), maximumNormalizedRadius: Math.max(...radii),
      coreToFront: Math.min(...radii) <= .5 && Math.max(...radii) >= .75 };
  }).sort((first, second) => second.nodeCount - first.nodeCount || second.edgeCount - first.edgeCount
    || first.minimumNormalizedRadius - second.minimumNormalizedRadius);
  const largest = componentRecords[0] || null;
  const degree = new Array(centers.length).fill(0);
  edges.forEach((edge) => { degree[edge.first]++; degree[edge.second]++; });
  const thresholdNodes = new Set(radialRecords.map((record, index) => record.clearance >= declaredThreshold ? index : null)
    .filter((index) => index !== null));
  const thresholdEdges = edges.filter((edge) => edge.throatClearance >= declaredThreshold
    && thresholdNodes.has(edge.first) && thresholdNodes.has(edge.second));
  const thresholdParents = centers.map((_, index) => index);
  const thresholdRoot = (index) => { while (thresholdParents[index] !== index) {
    thresholdParents[index] = thresholdParents[thresholdParents[index]]; index = thresholdParents[index];
  } return index; };
  thresholdEdges.forEach((edge) => {
    const first = thresholdRoot(edge.first); const second = thresholdRoot(edge.second);
    if (first !== second) thresholdParents[Math.max(first, second)] = Math.min(first, second);
  });
  const thresholdComponents = new Map();
  thresholdNodes.forEach((index) => {
    const key = thresholdRoot(index); if (!thresholdComponents.has(key)) thresholdComponents.set(key, []);
    thresholdComponents.get(key).push(index);
  });
  const thresholdComponentRecords = [...thresholdComponents.values()].map((nodes) => {
    const radii = nodes.map((node) => radialRecords[node].normalizedRadius);
    return { nodes, nodeCount: nodes.length,
      coreToFront: Math.min(...radii) <= .5 && Math.max(...radii) >= .75 };
  }).sort((first, second) => second.nodeCount - first.nodeCount);
  const widestPath = (nodeField, edgeField) => {
    const adjacency = centers.map(() => []);
    edges.forEach((edge) => {
      if (!Number.isFinite(edge[edgeField])) return;
      adjacency[edge.first].push({ node: edge.second, capacity: edge[edgeField] });
      adjacency[edge.second].push({ node: edge.first, capacity: edge[edgeField] });
    });
    const widest = new Array(centers.length).fill(-Infinity);
    radialRecords.forEach((record, index) => {
      if (record.normalizedRadius <= .5 && Number.isFinite(record[nodeField])) widest[index] = record[nodeField];
    });
    const visited = new Set();
    for (;;) {
      let selected = -1;
      for (let index = 0; index < widest.length; index++) if (!visited.has(index)
        && widest[index] > (selected < 0 ? -Infinity : widest[selected])) selected = index;
      if (selected < 0 || !Number.isFinite(widest[selected])) break;
      visited.add(selected);
      adjacency[selected].forEach((neighbor) => {
        const capacity = Math.min(widest[selected], neighbor.capacity, radialRecords[neighbor.node][nodeField]);
        if (capacity > widest[neighbor.node]) widest[neighbor.node] = capacity;
      });
    }
    const value = Math.max(-Infinity, ...radialRecords.map((record, index) =>
      record.normalizedRadius >= .75 ? widest[index] : -Infinity));
    return Number.isFinite(value) ? value : null;
  };
  const coreToFrontBottleneck = widestPath("clearance", "throatClearance");
  const stericCoreToFrontBottleneck = frameworkRadii ? widestPath("stericClearance", "stericThroatClearance") : null;
  const fittedStericCoreToFrontBottleneck = fittedFrameworkRadii
    ? widestPath("fittedStericClearance", "fittedStericThroatClearance") : null;
  const throatClearances = edges.map((edge) => edge.throatClearance);
  const stericThroatClearances = edges.map((edge) => edge.stericThroatClearance).filter(Number.isFinite);
  const fittedStericThroatClearances = edges.map((edge) => edge.fittedStericThroatClearance).filter(Number.isFinite);
  return {
    nodeCount: centers.length,
    edgeCount: edges.length,
    componentCount: componentRecords.length,
    isolatedNodeCount: degree.filter((value) => value === 0).length,
    isolatedNodeFraction: degree.filter((value) => value === 0).length / Math.max(1, centers.length),
    meanDegree: degree.reduce((sum, value) => sum + value, 0) / Math.max(1, centers.length),
    cycleRank: Math.max(0, edges.length - centers.length + componentRecords.length),
    largestComponentNodes: largest?.nodeCount || 0,
    largestComponentFraction: (largest?.nodeCount || 0) / Math.max(1, centers.length),
    coreToFrontComponentCount: componentRecords.filter((component) => component.coreToFront).length,
    minimumThroatClearance: throatClearances.length ? Math.min(...throatClearances) : null,
    percentile10ThroatClearance: quantile(throatClearances, .1),
    medianThroatClearance: quantile(throatClearances, .5),
    widestCoreToFrontClearance: coreToFrontBottleneck,
    minimumStericThroatClearance: stericThroatClearances.length ? Math.min(...stericThroatClearances) : null,
    percentile10StericThroatClearance: quantile(stericThroatClearances, .1),
    medianStericThroatClearance: quantile(stericThroatClearances, .5),
    widestStericCoreToFrontClearance: stericCoreToFrontBottleneck,
    minimumFittedStericThroatClearance: fittedStericThroatClearances.length
      ? Math.min(...fittedStericThroatClearances) : null,
    percentile10FittedStericThroatClearance: quantile(fittedStericThroatClearances, .1),
    medianFittedStericThroatClearance: quantile(fittedStericThroatClearances, .5),
    widestFittedStericCoreToFrontClearance: fittedStericCoreToFrontBottleneck,
    declaredThreshold,
    thresholdNodeCount: thresholdNodes.size,
    thresholdEdgeCount: thresholdEdges.length,
    thresholdComponentCount: thresholdComponentRecords.length,
    thresholdLargestComponentNodes: thresholdComponentRecords[0]?.nodeCount || 0,
    thresholdCoreToFrontComponentCount: thresholdComponentRecords.filter((component) => component.coreToFront).length,
    degrees: degree,
    edges,
    components: componentRecords,
    adjacencyDefinition: `two empty centers are adjacent only when witnessed simplices share a complete ${dimension === 2 ? "edge (two sites)" : "face (three sites)"}`,
    throatDefinition: "minimum distance from any explicit point site to the straight segment joining adjacent empty centers, divided by supplied nearest-neighbor distance",
    stericThroatDefinition: frameworkRadii
      ? "minimum distance from the straight center-to-center segment to any explicit species-dependent covalent-radius envelope, divided by supplied nearest-neighbor distance"
      : null,
    fittedStericThroatDefinition: fittedFrameworkRadii
      ? "minimum distance from the straight center-to-center segment to any sample-fitted additive species contact envelope, divided by supplied nearest-neighbor distance"
      : null,
  };
}

function summarize(positions, dimension, maximumAnchors, neighborLimit, histogramBins, histogramMaximum,
  declaredThreshold, frameworkRadii, fittedFrameworkRadii, displacementTensors) {
  const anchors = canonicalAnchors(positions, maximumAnchors);
  const centers = witnessedEmptyCenters(positions, dimension, maximumAnchors, neighborLimit, anchors);
  const structureCenter = centroid(positions);
  const maximumStructureRadius = Math.max(1e-12, ...positions.map((point) => Math.sqrt(squaredDistance(point, structureCenter))));
  const records = centers.map((record) => ({ clearance: record.clearance,
    stericClearance: frameworkRadii
      ? Math.min(...positions.map((point, index) => Math.sqrt(squaredDistance(record.center, point)) - frameworkRadii[index])) : null,
    fittedStericClearance: fittedFrameworkRadii
      ? Math.min(...positions.map((point, index) => Math.sqrt(squaredDistance(record.center, point))
        - fittedFrameworkRadii[index])) : null,
    clearanceModels: clearanceModelsAtPoint(record.center, positions, frameworkRadii, fittedFrameworkRadii,
      displacementTensors),
    normalizedRadius: Math.sqrt(squaredDistance(record.center, structureCenter)) / maximumStructureRadius }));
  const network = emptyCenterNetwork(centers, records, dimension, positions, declaredThreshold,
    frameworkRadii, fittedFrameworkRadii, displacementTensors);
  const clearances = records.map((record) => record.clearance);
  const core = records.filter((record) => record.normalizedRadius <= .5).map((record) => record.clearance);
  const front = records.filter((record) => record.normalizedRadius >= .75).map((record) => record.clearance);
  const histogram = new Array(histogramBins).fill(0);
  clearances.forEach((clearance) => { histogram[Math.min(histogramBins - 1,
    Math.max(0, Math.floor(clearance / histogramMaximum * histogramBins)))]++; });
  return {
    candidateCenters: records.length,
    sampledAnchors: anchors.length,
    medianClearance: quantile(clearances, .5),
    percentile90Clearance: quantile(clearances, .9),
    maximumClearance: clearances.length ? Math.max(...clearances) : null,
    coreMedianClearance: quantile(core, .5),
    frontMedianClearance: quantile(front, .5),
    radialRecords: records,
    histogram,
    network,
  };
}

export function interstitialClearanceAudit(currentPositions, referencePositions, {
  dimension = 3, maximumAnchors = 64, neighborLimit = 6, histogramBins = 20,
  histogramMaximum = 1.5, declaredThreshold = .5, currentSpecies = null,
  referenceSpecies = null, covalentRadiiAngstrom = null,
  fittedContactRadiiAngstrom = null,
  currentDisplacementTensorsAngstrom2 = null,
  referenceDisplacementTensorsAngstrom2 = null,
  physicalNearestNeighborAngstrom = null,
  periodicCellVectorsAngstrom = null, periodicAxes = null, includePeriodicReference = false,
} = {}) {
  const resolvedDimension = dimension === 2 ? 2 : 3;
  const minimumSites = resolvedDimension + 2;
  if (currentPositions.length < minimumSites || referencePositions.length < minimumSites) return {
    available: false, reason: `at least ${minimumSites} current and reference sites are required`,
    dimension: resolvedDimension, targetUsed: false,
  };
  const referenceScale = referenceNearestNeighborScale(referencePositions, maximumAnchors);
  if (!Number.isFinite(referenceScale) || referenceScale <= 1e-12) return {
    available: false, reason: "a positive supplied nearest-neighbor scale is required",
    dimension: resolvedDimension, targetUsed: false,
  };
  const normalize = (positions) => positions.map((point) => point.map((value) => value / referenceScale));
  const radiusNormalizationScale = Number.isFinite(physicalNearestNeighborAngstrom)
    && physicalNearestNeighborAngstrom > 1e-12 ? physicalNearestNeighborAngstrom : referenceScale;
  const normalizedRadii = (species, positions, radiusMap) => Array.isArray(species) && species.length === positions.length
    && radiusMap && species.every((symbol) => Number.isFinite(radiusMap[symbol]) && radiusMap[symbol] >= 0)
    ? species.map((symbol) => radiusMap[symbol] / radiusNormalizationScale) : null;
  const currentFrameworkRadii = normalizedRadii(currentSpecies, currentPositions, covalentRadiiAngstrom);
  const referenceFrameworkRadii = normalizedRadii(referenceSpecies, referencePositions, covalentRadiiAngstrom);
  const currentFittedFrameworkRadii = normalizedRadii(currentSpecies, currentPositions, fittedContactRadiiAngstrom);
  const referenceFittedFrameworkRadii = normalizedRadii(referenceSpecies, referencePositions, fittedContactRadiiAngstrom);
  const currentDisplacementTensors = normalizeDisplacementTensors(currentDisplacementTensorsAngstrom2,
    currentPositions.length, radiusNormalizationScale);
  const referenceDisplacementTensors = normalizeDisplacementTensors(referenceDisplacementTensorsAngstrom2,
    referencePositions.length, radiusNormalizationScale);
  const current = summarize(normalize(currentPositions), resolvedDimension, maximumAnchors,
    neighborLimit, histogramBins, histogramMaximum, declaredThreshold, currentFrameworkRadii,
    currentFittedFrameworkRadii, currentDisplacementTensors);
  const reference = summarize(normalize(referencePositions), resolvedDimension, maximumAnchors,
    neighborLimit, histogramBins, histogramMaximum, declaredThreshold, referenceFrameworkRadii,
    referenceFittedFrameworkRadii, referenceDisplacementTensors);
  const normalizedPeriodicCell = Array.isArray(periodicCellVectorsAngstrom)
    && periodicCellVectorsAngstrom.length === 3
    ? periodicCellVectorsAngstrom.map((vector) => vector.map((value) => value / radiusNormalizationScale)) : null;
  const referencePeriodic = includePeriodicReference ? periodicWitnessedSummary(normalize(referencePositions),
    resolvedDimension, maximumAnchors, neighborLimit, declaredThreshold, referenceFrameworkRadii,
    referenceFittedFrameworkRadii, referenceDisplacementTensors,
    normalizedPeriodicCell, periodicAxes) : null;
  if (!reference.candidateCenters || (!current.candidateCenters && !referencePeriodic)) return {
    available: false, reason: "no nondegenerate locally witnessed empty simplex centers were resolved",
    dimension: resolvedDimension, currentCandidateCenters: current.candidateCenters,
    referenceCandidateCenters: reference.candidateCenters, targetUsed: false,
  };
  return {
    available: true,
    dimension: resolvedDimension,
    currentSites: currentPositions.length,
    referenceSites: referencePositions.length,
    referenceNearestNeighborScale: referenceScale,
    maximumAnchors,
    neighborLimit,
    histogramBins,
    histogramMaximum,
    declaredThreshold,
    histogramOverflowIncludedInLastBin: true,
    ...current,
    reference,
    referencePeriodic,
    finiteCurrentNetworkAvailable: current.candidateCenters > 0,
    clearanceDefinition: "empty circumcircle/circumsphere center clearance divided by supplied median nearest-neighbor distance",
    candidateDefinition: "nondegenerate local simplices from an invariant radial anchor sample and its nearest-neighbor tie set; center retained only inside the simplex and empty of explicit sites",
    finiteObservationNoPeriodicImages: true,
    periodicReferenceQuotientAvailable: Boolean(referencePeriodic),
    periodicReferenceUsesReportedCellOnly: Boolean(referencePeriodic),
    periodicCurrentGrowthWrapped: false,
    pointSitesNoAtomicRadii: true,
    covalentRadiusStericModelAvailable: Boolean(currentFrameworkRadii && referenceFrameworkRadii),
    fittedContactRadiusStericModelAvailable: Boolean(currentFittedFrameworkRadii && referenceFittedFrameworkRadii),
    fittedContactRadiusNormalizationScaleAngstrom: currentFittedFrameworkRadii && referenceFittedFrameworkRadii
      ? radiusNormalizationScale : null,
    fittedContactRadiusDefinition: currentFittedFrameworkRadii && referenceFittedFrameworkRadii
      ? "sample-fitted additive leading-contact envelopes; Cordero ratios used only as a ridge prior" : null,
    displacementEnvelopeAvailable: Boolean(currentDisplacementTensors?.some(Boolean)
      || referenceDisplacementTensors?.some(Boolean)),
    currentDisplacementTensorSites: currentDisplacementTensors?.filter(Boolean).length || 0,
    referenceDisplacementTensorSites: referenceDisplacementTensors?.filter(Boolean).length || 0,
    displacementSigmaMultipliers: [...DISPLACEMENT_SIGMA_MULTIPLIERS],
    displacementUnknownSitesUseZeroSupport: true,
    displacementEnvelopeDefinition: "directional k sqrt(n^T U n) support from reported Cartesian Uiso/Uij mean-square displacement tensors",
    displacementEnvelopeIsTrajectory: false,
    displacementEnvelopeIsTemperature: false,
    displacementEnvelopeIsProbabilityOrConfidenceRegion: false,
    displacementEnvelopeTranslationInvariant: true,
    displacementEnvelopeProperRotationInvariantWhenTensorRotatesWithSites: true,
    covalentRadiusNormalizationScaleAngstrom: currentFrameworkRadii && referenceFrameworkRadii
      ? radiusNormalizationScale : null,
    covalentRadiusSource: currentFrameworkRadii && referenceFrameworkRadii
      ? "Cordero et al., Dalton Transactions (2008), DOI 10.1039/B801115J; element-only covalent-radius proxy" : null,
    oxidationStateOrCoordinationSpecificRadiiUsed: false,
    covalentRadiusStericTranslationInvariant: true,
    covalentRadiusStericProperRotationInvariant: true,
    covalentRadiusStericAtomPermutationInvariant: true,
    covalentRadiusStericUniformCoordinateScalingInvariant: false,
    translationInvariant: true,
    properRotationInvariant: true,
    atomPermutationInvariant: true,
    uniformScaleInvariantWhenCurrentAndReferenceShareScale: true,
    targetUsed: false,
    usedAsGrowthInput: false,
    porosityInferred: false,
    poreVolumeInferred: false,
    accessibleFreeVolumeInferred: false,
    vacancyOrInterstitialIdentityInferred: false,
    diffusionPathInferred: false,
    migrationBarrierInferred: false,
    physicalTransportConnectivityInferred: false,
    probeAccessibleNetworkInferred: false,
    pressureInferred: false,
    physicalTimeIntegrated: false,
  };
}
