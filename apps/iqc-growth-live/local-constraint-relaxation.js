const pairKey = (first, second) => first < second ? `${first}|${second}` : `${second}|${first}`;
const length = (vector) => Math.hypot(...vector);
const subtract = (first, second) => first.map((value, axis) => value - second[axis]);
const addScaled = (point, vector, scale) => point.map((value, axis) => value + scale * vector[axis]);

function contactGraph(sites, distanceModel) {
  const graph = [];
  for (let first = 0; first < sites.length; first++) for (let second = first + 1; second < sites.length; second++) {
    if (!(sites[first].movable || sites[second].movable)) continue;
    const record = distanceModel?.byKey?.[pairKey(sites[first].species, sites[second].species)];
    if (!record) continue;
    const delta = subtract(sites[second].position, sites[first].position);
    const distance = length(delta);
    const cutoff = Math.max(record.upperContact * 1.18,
      record.typicalContact + 3 * record.contactScale);
    if (!(distance > 1e-9 && distance <= cutoff)) continue;
    graph.push(Object.freeze({
      first, second, target: record.typicalContact,
      scale: Math.max(record.contactScale, record.typicalContact * .04, 1e-6),
    }));
  }
  return graph;
}

function contactObjective(positions, graph) {
  return graph.reduce((sum, edge) => {
    const residual = (length(subtract(positions[edge.second], positions[edge.first])) - edge.target) / edge.scale;
    return sum + residual * residual;
  }, 0) / Math.max(1, graph.length);
}

function totalObjective(positions, originals, movable, graph, cap, tetherWeight) {
  const contact = contactObjective(positions, graph);
  const tether = positions.reduce((sum, point, index) => movable[index]
    ? sum + (length(subtract(point, originals[index])) / Math.max(cap, 1e-9)) ** 2 : sum, 0)
    / Math.max(1, movable.filter(Boolean).length);
  return contact + tetherWeight * tether;
}

function gradientFor(positions, originals, movable, graph, cap, tetherWeight) {
  const gradient = positions.map(() => [0, 0, 0]);
  graph.forEach((edge) => {
    const delta = subtract(positions[edge.second], positions[edge.first]);
    const distance = length(delta);
    if (!(distance > 1e-12)) return;
    const coefficient = 2 * (distance - edge.target) / (edge.scale * edge.scale * distance * Math.max(1, graph.length));
    delta.forEach((value, axis) => {
      if (movable[edge.first]) gradient[edge.first][axis] -= coefficient * value;
      if (movable[edge.second]) gradient[edge.second][axis] += coefficient * value;
    });
  });
  const movableCount = Math.max(1, movable.filter(Boolean).length);
  positions.forEach((point, index) => {
    if (!movable[index]) return;
    const offset = subtract(point, originals[index]);
    offset.forEach((value, axis) => {
      gradient[index][axis] += 2 * tetherWeight * value / (Math.max(cap, 1e-9) ** 2 * movableCount);
    });
  });
  return gradient;
}

function cappedPositions(positions, originals, movable, gradient, step, cap) {
  return positions.map((point, index) => {
    if (!movable[index]) return [...point];
    let trial = addScaled(point, gradient[index], -step);
    const offset = subtract(trial, originals[index]);
    const displacement = length(offset);
    if (displacement > cap) trial = addScaled(originals[index], offset, cap / displacement);
    return trial;
  });
}

export function relaxLocalContactGeometry(rawSites, distanceModel, {
  displacementCap,
  maximumIterations = 12,
  tetherWeight = .08,
  initialOffsets = null,
} = {}) {
  if (!Array.isArray(rawSites) || !rawSites.length) throw new Error("local relaxation requires sites");
  if (!(Number.isFinite(displacementCap) && displacementCap > 0)) throw new Error("local relaxation requires a positive displacement cap");
  if (!(Number.isInteger(maximumIterations) && maximumIterations > 0 && maximumIterations <= 64)) {
    throw new Error("local relaxation iteration count must be an integer in [1,64]");
  }
  const sites = rawSites.map((site) => ({
    species: String(site.species), movable: Boolean(site.movable),
    position: site.position.map(Number),
  }));
  if (sites.some((site) => site.position.length !== 3 || site.position.some((value) => !Number.isFinite(value)))) {
    throw new Error("local relaxation positions must be finite Cartesian triples");
  }
  const movable = sites.map((site) => site.movable);
  if (!movable.some(Boolean)) return Object.freeze({ accepted: false, reason: "no movable sites", positions: sites.map((site) => site.position) });
  const graph = contactGraph(sites, distanceModel);
  const originals = sites.map((site) => [...site.position]);
  const suppliedOffsets = Array.isArray(initialOffsets) && initialOffsets.length === sites.length
    ? initialOffsets.map((offset, index) => {
      if (!movable[index] || !Array.isArray(offset)) return [0, 0, 0];
      const vector = offset.map(Number);
      if (vector.length !== 3 || vector.some((value) => !Number.isFinite(value))) return [0, 0, 0];
      const magnitude = length(vector);
      return magnitude > displacementCap ? vector.map((value) => value * displacementCap / magnitude) : vector;
    }) : sites.map(() => [0, 0, 0]);
  let positions = originals.map((point, index) => addScaled(point, suppliedOffsets[index], 1));
  const initialContactObjective = contactObjective(positions, graph);
  const unseededContactObjective = contactObjective(originals, graph);
  const unseededObjective = totalObjective(originals, originals, movable, graph, displacementCap, tetherWeight);
  const seededObjective = totalObjective(positions, originals, movable, graph, displacementCap, tetherWeight);
  const seedImprovedObjective = seededObjective < unseededObjective - 1e-12;
  if (!seedImprovedObjective) positions = originals.map((point) => [...point]);
  const seedSites = suppliedOffsets.filter((offset) => length(offset) > 1e-12).length;
  if (graph.length < 2 || !(unseededContactObjective > 1e-12)) return Object.freeze({
    accepted: false, reason: graph.length < 2 ? "insufficient learned contacts" : "already contact-compatible",
    positions: originals.map((point) => [...point]), contactTerms: graph.length,
    initialContactObjective: unseededContactObjective, finalContactObjective: unseededContactObjective,
    initialSeedSupplied: seedSites > 0, initialSeedAccepted: false, initialSeedSites: seedSites,
    observedSeedSupplied: seedSites > 0, observedSeedAccepted: false, observedSeedSites: seedSites,
    iterations: 0, maximumDisplacement: 0, rmsDisplacement: 0,
  });
  let objective = seedImprovedObjective ? seededObjective : unseededObjective;
  let acceptedSteps = 0;
  for (let iteration = 0; iteration < maximumIterations; iteration++) {
    const gradient = gradientFor(positions, originals, movable, graph, displacementCap, tetherWeight);
    const maximumGradient = Math.max(...gradient.filter((_, index) => movable[index]).map(length), 0);
    if (!(maximumGradient > 1e-12)) break;
    let step = displacementCap * .32 / maximumGradient;
    let improved = false;
    for (let attempt = 0; attempt < 10; attempt++) {
      const trial = cappedPositions(positions, originals, movable, gradient, step, displacementCap);
      const trialObjective = totalObjective(trial, originals, movable, graph, displacementCap, tetherWeight);
      if (trialObjective < objective - 1e-12) {
        positions = trial; objective = trialObjective; acceptedSteps++; improved = true; break;
      }
      step *= .5;
    }
    if (!improved) break;
  }
  const displacements = positions.map((point, index) => movable[index]
    ? length(subtract(point, originals[index])) : 0);
  const movableDisplacements = displacements.filter((_, index) => movable[index]);
  const finalContactObjective = contactObjective(positions, graph);
  const accepted = (acceptedSteps > 0 || seedImprovedObjective)
    && finalContactObjective < unseededContactObjective - 1e-9;
  return Object.freeze({
    accepted, reason: accepted ? "contact residual reduced" : "no monotone contact projection",
    positions: positions.map(Object.freeze), contactTerms: graph.length,
    initialContactObjective: unseededContactObjective, finalContactObjective, iterations: acceptedSteps,
    initialSeedSupplied: seedSites > 0,
    initialSeedAccepted: seedImprovedObjective,
    initialSeedSites: seedSites,
    initialSeedContactObjective: initialContactObjective,
    observedSeedSupplied: seedSites > 0,
    observedSeedAccepted: seedImprovedObjective,
    observedSeedSites: seedSites,
    observedSeedContactObjective: initialContactObjective,
    maximumDisplacement: Math.max(...movableDisplacements, 0),
    rmsDisplacement: Math.sqrt(movableDisplacements.reduce((sum, value) => sum + value * value, 0)
      / Math.max(1, movableDisplacements.length)),
  });
}
