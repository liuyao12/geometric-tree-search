function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function positive(value, label) {
  const number = finite(value, label);
  if (!(number > 0)) throw new RangeError(`${label} must be positive`);
  return number;
}

function integer(value, label, minimum, maximum) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < minimum || number > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}`);
  }
  return number;
}

function text(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function vector(value, label) {
  if (!Array.isArray(value) || value.length !== 3) throw new TypeError(`${label} must be a 3-vector`);
  return value.map((entry, axis) => finite(entry, `${label}[${axis}]`));
}

const subtract = (first, second) => first.map((value, axis) => value - second[axis]);
const add = (first, second) => first.map((value, axis) => value + second[axis]);
const scale = (value, factor) => value.map(entry => entry * factor);
const dot = (first, second) => first.reduce((sum, value, axis) => sum + value * second[axis], 0);
const cross = (first, second) => [first[1] * second[2] - first[2] * second[1],
  first[2] * second[0] - first[0] * second[2],
  first[0] * second[1] - first[1] * second[0]];
const norm = value => Math.hypot(...value);
const distance = (first, second) => norm(subtract(first, second));
const normalize = value => scale(value, 1 / norm(value));

function frame(first, second, third) {
  const e1 = normalize(subtract(second, first));
  const raw = subtract(third, first);
  const rejection = subtract(raw, scale(e1, dot(raw, e1)));
  if (!(norm(rejection) > 1e-8)) return null;
  const e2 = normalize(rejection);
  const e3 = cross(e1, e2);
  return [e1, e2, e3];
}

function rotationFromFrames(local, world) {
  // Frames are stored as basis vectors. R = W L^T.
  return Array.from({ length: 3 }, (_, row) => Array.from({ length: 3 }, (_, column) =>
    world.reduce((sum, basis, axis) => sum + basis[row] * local[axis][column], 0)));
}

function applyRotation(matrix, point) {
  return matrix.map(row => dot(row, point));
}

function determinant(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

function anchorTriplet(sites) {
  let best = null;
  for (let first = 0; first < sites.length; first += 1) {
    for (let second = first + 1; second < sites.length; second += 1) {
      for (let third = second + 1; third < sites.length; third += 1) {
        const area2 = norm(cross(subtract(sites[second].positionAngstrom,
          sites[first].positionAngstrom), subtract(sites[third].positionAngstrom,
          sites[first].positionAngstrom)));
        const span = Math.max(distance(sites[first].positionAngstrom, sites[second].positionAngstrom),
          distance(sites[first].positionAngstrom, sites[third].positionAngstrom),
          distance(sites[second].positionAngstrom, sites[third].positionAngstrom));
        const score = area2 * span;
        const key = [sites[first].species, sites[second].species, sites[third].species,
          first, second, third].join("|");
        if (score > 1e-10 && (!best || score > best.score + 1e-12
            || Math.abs(score - best.score) <= 1e-12 && key < best.key)) {
          best = { indices: [first, second, third], score, key };
        }
      }
    }
  }
  return best;
}

function normalizeGrammar(grammar) {
  if (grammar?.schema !== "gcts-frozen-local-port-grammar-v1" || grammar?.targetUsed) {
    throw new Error("a frozen target-blind local port grammar is required");
  }
  const metricToleranceAngstrom = positive(grammar.metricToleranceAngstrom,
    "grammar metric tolerance");
  const typeIds = new Set();
  const prototypes = (grammar.prototypes || []).map((prototype, prototypeIndex) => {
    const typeId = integer(prototype.typeId, `prototype ${prototypeIndex} type`, 0, 1_000_000);
    if (typeIds.has(typeId)) throw new Error(`duplicate grammar prototype type ${typeId}`);
    typeIds.add(typeId);
    const sites = (prototype.sites || []).map((site, siteIndex) => ({
      species: text(site.species, `prototype ${typeId} site ${siteIndex} species`),
      positionAngstrom: vector(site.positionAngstrom,
        `prototype ${typeId} site ${siteIndex} position`),
    }));
    if (sites.length < 2) throw new Error(`prototype ${typeId} needs at least two sites`);
    return { typeId, occurrenceIndex: Number.isInteger(prototype.occurrenceIndex)
      ? prototype.occurrenceIndex : null, sites,
    outgoingRuleCount: integer(prototype.outgoingRuleCount || 0,
      `prototype ${typeId} outgoing rules`, 0, 1_000_000),
    incomingRuleCount: integer(prototype.incomingRuleCount || 0,
      `prototype ${typeId} incoming rules`, 0, 1_000_000),
    anchor: anchorTriplet(sites) };
  });
  const admittedConnections = new Set((grammar.admittedConnections || []).map((connection, index) => {
    const fromType = integer(connection.fromType, `connection ${index} source`, 0, 1_000_000);
    const toType = integer(connection.toType, `connection ${index} target`, 0, 1_000_000);
    if (!typeIds.has(fromType) || !typeIds.has(toType)) {
      throw new Error(`connection ${index} references an unknown type`);
    }
    return `${fromType}>${toType}`;
  }));
  return { metricToleranceAngstrom, prototypes, admittedConnections,
    minimumSharedAtoms: integer(grammar.minimumSharedAtoms ?? 2,
      "minimum shared atoms", 1, 64),
  structureSha256: text(grammar.structureSha256, "grammar structure SHA-256") };
}

function siteGrid(sites, cellSize) {
  const map = new Map();
  const cell = point => point.map(value => Math.floor(value / cellSize));
  sites.forEach((site, index) => {
    const [x, y, z] = cell(site.positionAngstrom);
    const key = `${site.species}|${x}|${y}|${z}`;
    const bucket = map.get(key) || []; bucket.push(index); map.set(key, bucket);
  });
  return { query(species, point) {
    const [cx, cy, cz] = cell(point); const matches = [];
    for (let x = cx - 1; x <= cx + 1; x += 1) for (let y = cy - 1; y <= cy + 1; y += 1) {
      for (let z = cz - 1; z <= cz + 1; z += 1) {
        matches.push(...(map.get(`${species}|${x}|${y}|${z}`) || []));
      }
    }
    return matches;
  } };
}

function fitOccurrence(prototype, nucleusSites, grid, worldAnchorIndices, tolerance) {
  const localAnchor = prototype.anchor.indices.map(index => prototype.sites[index].positionAngstrom);
  const worldAnchor = worldAnchorIndices.map(index => nucleusSites[index].positionAngstrom);
  const localFrame = frame(...localAnchor); const worldFrame = frame(...worldAnchor);
  if (!localFrame || !worldFrame) return null;
  const rotationMatrix = rotationFromFrames(localFrame, worldFrame);
  if (Math.abs(determinant(rotationMatrix) - 1) > 1e-8) return null;
  const translationAngstrom = subtract(worldAnchor[0],
    applyRotation(rotationMatrix, localAnchor[0]));
  const used = new Set(); const supportSiteIndices = []; const residuals = [];
  for (const prototypeSite of prototype.sites) {
    const predicted = add(applyRotation(rotationMatrix, prototypeSite.positionAngstrom),
      translationAngstrom);
    const match = grid.query(prototypeSite.species, predicted)
      .filter(index => !used.has(index))
      .map(index => ({ index, residual: distance(nucleusSites[index].positionAngstrom, predicted) }))
      .filter(candidate => candidate.residual <= tolerance)
      .sort((first, second) => first.residual - second.residual || first.index - second.index)[0];
    if (!match) return null;
    used.add(match.index); supportSiteIndices.push(match.index); residuals.push(match.residual);
  }
  const rmsdAngstrom = Math.sqrt(residuals.reduce((sum, value) => sum + value * value, 0)
    / residuals.length);
  return { typeId: prototype.typeId, occurrenceIndex: prototype.occurrenceIndex,
    supportSiteIndices: supportSiteIndices.sort((a, b) => a - b), rotationMatrix,
    translationAngstrom, rmsdAngstrom, maximumResidualAngstrom: Math.max(...residuals),
    outgoingRuleCount: prototype.outgoingRuleCount,
    incomingRuleCount: prototype.incomingRuleCount };
}

function occurrenceComponents(selected, admittedConnections, minimumSharedAtoms) {
  const adjacency = selected.map(() => new Set());
  const edges = [];
  for (let first = 0; first < selected.length; first += 1) {
    const firstSupport = new Set(selected[first].supportSiteIndices);
    for (let second = first + 1; second < selected.length; second += 1) {
      const sharedAtoms = selected[second].supportSiteIndices
        .filter(index => firstSupport.has(index)).length;
      const forward = admittedConnections.has(`${selected[first].typeId}>${selected[second].typeId}`);
      const reverse = admittedConnections.has(`${selected[second].typeId}>${selected[first].typeId}`);
      if (sharedAtoms < minimumSharedAtoms || !forward && !reverse) continue;
      adjacency[first].add(second); adjacency[second].add(first);
      edges.push({ firstOccurrenceId: selected[first].occurrenceId,
        secondOccurrenceId: selected[second].occurrenceId, sharedAtoms,
        forwardAdmitted: forward, reverseAdmitted: reverse });
    }
  }
  const components = []; const seen = new Set();
  selected.forEach((_, start) => {
    if (seen.has(start)) return;
    const queue = [start]; const members = []; seen.add(start);
    while (queue.length) {
      const current = queue.shift(); members.push(selected[current].occurrenceId);
      adjacency[current].forEach(next => { if (!seen.has(next)) { seen.add(next); queue.push(next); } });
    }
    components.push(members.sort());
  });
  return { edges, components };
}

export function auditCriticalNucleusGrammarAdmission(geometry, frozenGrammar, options = {}) {
  if (geometry?.schema !== "gcts-critical-nucleus-geometry-evidence-v1"
      || geometry?.targetUsed || geometry?.gctsSeedChanged) {
    throw new Error("validated target-blind critical-nucleus geometry is required");
  }
  const grammar = normalizeGrammar(frozenGrammar);
  if (geometry.structureSha256 !== grammar.structureSha256) {
    throw new Error("critical-nucleus geometry and frozen grammar structure mismatch");
  }
  const minimumRecognizedFraction = finite(options.minimumRecognizedFraction ?? .8,
    "minimum recognized fraction");
  if (minimumRecognizedFraction < 0 || minimumRecognizedFraction > 1) {
    throw new RangeError("minimum recognized fraction must be in [0,1]");
  }
  const maximumAnchorPairChecks = integer(options.maximumAnchorPairChecks ?? 2_000_000,
    "anchor-pair check cap", 1, 100_000_000);
  const maximumAnchorTriples = integer(options.maximumAnchorTriples ?? 200_000,
    "anchor-triple cap", 1, 10_000_000);
  const maximumOccurrences = integer(options.maximumOccurrences ?? 20_000,
    "occurrence cap", 1, 1_000_000);
  const nucleusSites = geometry.sites.map((site, index) => ({
    index, siteId: text(site.siteId, `nucleus site ${index} ID`),
    species: text(site.species, `nucleus site ${index} species`),
    positionAngstrom: vector(site.positionAngstrom, `nucleus site ${index} position`),
  }));
  const bySpecies = new Map();
  nucleusSites.forEach((site, index) => {
    const list = bySpecies.get(site.species) || []; list.push(index); bySpecies.set(site.species, list);
  });
  const grid = siteGrid(nucleusSites, grammar.metricToleranceAngstrom);
  const occurrences = []; const occurrenceKeys = new Set();
  let anchorPairChecks = 0; let anchorTriples = 0; let truncated = false;
  let unorientablePrototypeCount = 0;
  outer: for (const prototype of grammar.prototypes) {
    if (!prototype.anchor) { unorientablePrototypeCount += 1; continue; }
    const [firstLocalIndex, secondLocalIndex, thirdLocalIndex] = prototype.anchor.indices;
    const firstLocal = prototype.sites[firstLocalIndex];
    const secondLocal = prototype.sites[secondLocalIndex];
    const thirdLocal = prototype.sites[thirdLocalIndex];
    const firstCandidates = bySpecies.get(firstLocal.species) || [];
    const secondCandidates = bySpecies.get(secondLocal.species) || [];
    const thirdCandidates = bySpecies.get(thirdLocal.species) || [];
    const d12 = distance(firstLocal.positionAngstrom, secondLocal.positionAngstrom);
    const d13 = distance(firstLocal.positionAngstrom, thirdLocal.positionAngstrom);
    const d23 = distance(secondLocal.positionAngstrom, thirdLocal.positionAngstrom);
    for (const first of firstCandidates) for (const second of secondCandidates) {
      anchorPairChecks += 1;
      if (anchorPairChecks > maximumAnchorPairChecks) { truncated = true; break outer; }
      if (first === second || Math.abs(distance(nucleusSites[first].positionAngstrom,
        nucleusSites[second].positionAngstrom) - d12) > grammar.metricToleranceAngstrom) continue;
      for (const third of thirdCandidates) {
        if (third === first || third === second) continue;
        if (Math.abs(distance(nucleusSites[first].positionAngstrom,
          nucleusSites[third].positionAngstrom) - d13) > grammar.metricToleranceAngstrom
          || Math.abs(distance(nucleusSites[second].positionAngstrom,
            nucleusSites[third].positionAngstrom) - d23) > grammar.metricToleranceAngstrom) continue;
        anchorTriples += 1;
        if (anchorTriples > maximumAnchorTriples) { truncated = true; break outer; }
        const fitted = fitOccurrence(prototype, nucleusSites, grid, [first, second, third],
          grammar.metricToleranceAngstrom);
        if (!fitted) continue;
        const key = `${fitted.typeId}|${fitted.supportSiteIndices.join(",")}`;
        if (occurrenceKeys.has(key)) continue;
        occurrenceKeys.add(key);
        fitted.occurrenceId = `N${String(occurrences.length + 1).padStart(5, "0")}`;
        occurrences.push(fitted);
        if (occurrences.length >= maximumOccurrences) { truncated = true; break outer; }
      }
    }
  }
  const uncovered = new Set(nucleusSites.map(site => site.index));
  const available = [...occurrences]; const selected = [];
  while (available.length) {
    const ranked = available.map(occurrence => ({ occurrence,
      fresh: occurrence.supportSiteIndices.filter(index => uncovered.has(index)).length }))
      .filter(record => record.fresh > 0)
      .sort((first, second) => second.fresh - first.fresh
        || second.occurrence.outgoingRuleCount - first.occurrence.outgoingRuleCount
        || second.occurrence.supportSiteIndices.length - first.occurrence.supportSiteIndices.length
        || first.occurrence.rmsdAngstrom - second.occurrence.rmsdAngstrom
        || first.occurrence.occurrenceId.localeCompare(second.occurrence.occurrenceId));
    if (!ranked.length) break;
    const chosen = ranked[0].occurrence; selected.push(chosen);
    chosen.supportSiteIndices.forEach(index => uncovered.delete(index));
    available.splice(available.indexOf(chosen), 1);
  }
  const coveredAtomCount = nucleusSites.length - uncovered.size;
  const recognizedAtomFraction = coveredAtomCount / Math.max(1, nucleusSites.length);
  const residualSites = [...uncovered].sort((a, b) => a - b).map(index => ({
    siteIndex: index, siteId: nucleusSites[index].siteId, species: nucleusSites[index].species,
    positionAngstrom: [...nucleusSites[index].positionAngstrom], terminal: true }));
  const graph = occurrenceComponents(selected, grammar.admittedConnections,
    grammar.minimumSharedAtoms);
  const frontierPlacementCount = selected.filter(occurrence => occurrence.outgoingRuleCount > 0).length;
  const connectedRecognizedCover = selected.length <= 1 || graph.components.length === 1;
  const seedAdmissible = !truncated && selected.length > 0
    && recognizedAtomFraction >= minimumRecognizedFraction
    && frontierPlacementCount > 0 && connectedRecognizedCover;
  return {
    schema: "gcts-critical-nucleus-grammar-admission-v1",
    structureSha256: geometry.structureSha256,
    geometryRequestSha256: geometry.requestSha256,
    metricToleranceAngstrom: grammar.metricToleranceAngstrom,
    minimumRecognizedFraction,
    prototypeCount: grammar.prototypes.length,
    orientablePrototypeCount: grammar.prototypes.length - unorientablePrototypeCount,
    unorientablePrototypeCount,
    enumeratedOccurrenceCount: occurrences.length,
    selectedOccurrences: selected,
    selectedOccurrenceCount: selected.length,
    selectedTypeCount: new Set(selected.map(occurrence => occurrence.typeId)).size,
    admittedConnectionEdges: graph.edges,
    recognizedComponents: graph.components,
    connectedRecognizedCover,
    nucleusAtomCount: nucleusSites.length,
    coveredAtomCount,
    recognizedAtomFraction,
    residualAtomCount: residualSites.length,
    residualSites,
    completeRepresentationWithResidualTerminals:
      coveredAtomCount + residualSites.length === nucleusSites.length,
    frontierPlacementCount,
    totalOutgoingRules: selected.reduce((sum, occurrence) => sum + occurrence.outgoingRuleCount, 0),
    anchorPairChecks,
    anchorTriples,
    maximumAnchorPairChecks,
    maximumAnchorTriples,
    maximumOccurrences,
    truncated,
    seedAdmissible,
    targetUsed: false,
    candidateSetInspected: false,
    growthStateChanged: false,
    claimBoundary: seedAdmissible
      ? "The externally supplied nucleus has a connected, finite, proper-SE(3) frozen-grammar cover with explicit residual terminals and at least one admitted outward port. Admission still requires an explicit user action and a fresh live collision/boundary check."
      : "The externally supplied nucleus is not authorized as a GCTS seed under the declared frozen-grammar coverage and connectivity gate; no growth state changed.",
  };
}
