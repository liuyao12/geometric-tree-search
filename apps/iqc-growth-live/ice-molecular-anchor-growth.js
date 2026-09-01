const add = (left, right) => left.map((value, index) => value + right[index]);
const sub = (left, right) => left.map((value, index) => value - right[index]);
const distance = (left, right) => Math.hypot(...sub(left, right));
const transpose = (matrix) => matrix[0].map((_, column) => matrix.map((row) => row[column]));
const matvec = (matrix, vector) => matrix.map((row) => row.reduce((sum, value, index) => sum + value * vector[index], 0));
const matmul = (left, right) => left.map((row) => right[0].map((_, column) =>
  row.reduce((sum, value, index) => sum + value * right[index][column], 0)));
const DONOR_CONE_DEGREES = 35;

function determinant(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

function matrixResidual(matrix) {
  const product = matmul(transpose(matrix), matrix);
  return Math.max(...product.flatMap((row, first) => row.map((value, second) =>
    Math.abs(value - (first === second ? 1 : 0)))));
}

function sha256Ascii(message) {
  // Small synchronous SHA-256 for deterministic geometry keys. WebCrypto is
  // asynchronous and would make a single frontier update nondeterministic
  // relative to the Python audit. The payload contains ASCII JSON only.
  const rightRotate = (value, amount) => value >>> amount | value << (32 - amount);
  const primes = [];
  const hash = [];
  const composites = {};
  for (let candidate = 2; primes.length < 64; candidate++) {
    if (composites[candidate]) continue;
    primes.push(candidate);
    for (let multiple = candidate * candidate; multiple < 312; multiple += candidate) composites[multiple] = true;
  }
  primes.forEach((prime, index) => {
    if (index < 8) hash[index] = Math.floor((prime ** .5 % 1) * 2 ** 32);
  });
  const constants = primes.map((prime) => Math.floor((prime ** (1 / 3) % 1) * 2 ** 32));
  const bytes = [...message].map((character) => character.charCodeAt(0));
  const bitLength = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (let shift = 56; shift >= 0; shift -= 8) bytes.push(Math.floor(bitLength / 2 ** shift) & 255);
  for (let offset = 0; offset < bytes.length; offset += 64) {
    const words = new Array(64);
    for (let index = 0; index < 16; index++) words[index] = bytes.slice(offset + index * 4, offset + index * 4 + 4)
      .reduce((value, byte) => value << 8 | byte, 0);
    for (let index = 16; index < 64; index++) {
      const first = words[index - 15];
      const second = words[index - 2];
      const sigma0 = rightRotate(first, 7) ^ rightRotate(first, 18) ^ first >>> 3;
      const sigma1 = rightRotate(second, 17) ^ rightRotate(second, 19) ^ second >>> 10;
      words[index] = (words[index - 16] + sigma0 + words[index - 7] + sigma1) | 0;
    }
    let [a, b, c, d, e, f, g, h] = hash;
    for (let index = 0; index < 64; index++) {
      const upperSigma1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const choose = e & f ^ ~e & g;
      const temporary1 = (h + upperSigma1 + choose + constants[index] + words[index]) | 0;
      const upperSigma0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const majority = a & b ^ a & c ^ b & c;
      const temporary2 = (upperSigma0 + majority) | 0;
      [h, g, f, e, d, c, b, a] = [g, f, e, (d + temporary1) | 0, c, b, a, (temporary1 + temporary2) | 0];
    }
    [a, b, c, d, e, f, g, h].forEach((value, index) => { hash[index] = (hash[index] + value) | 0; });
  }
  return hash.map((value) => (value >>> 0).toString(16).padStart(8, "0")).join("");
}

function quantizedSitesKey(sites, tolerance) {
  const payload = sites.map(([species, point]) => [species, ...point.map((value) => Math.round(value / tolerance))])
    .sort((first, second) => {
      const color = first[0].localeCompare(second[0]);
      if (color) return color;
      for (let index = 1; index < first.length; index++) {
        if (first[index] !== second[index]) return first[index] - second[index];
      }
      return 0;
    });
  return sha256Ascii(JSON.stringify(payload));
}

function renderSites(artifact, occurrence) {
  return artifact.prototype.sites.map(([species, point]) => [species,
    add(matvec(occurrence.rotation, point), occurrence.translation)]);
}

function anchorSite(artifact, occurrence) {
  const anchorIndex = artifact.prototype.sites.findIndex(([species]) => species === "O");
  if (anchorIndex < 0 || artifact.prototype.sites.filter(([species]) => species === "O").length !== 1) {
    throw new Error("Frozen molecular prototype must have one geometry-derived oxygen anchor");
  }
  const [species, point] = artifact.prototype.sites[anchorIndex];
  return [species, add(matvec(occurrence.rotation, point), occurrence.translation)];
}

function dot(left, right) {
  return left.reduce((sum, value, index) => sum + value * right[index], 0);
}

function donorTowardAnchor(artifact, occurrence, neighborPoint) {
  const sites = renderSites(artifact, occurrence);
  const oxygen = sites.find(([species]) => species === "O")?.[1];
  const hydrogens = sites.filter(([species]) => species === "H").map(([, point]) => point);
  if (!oxygen || hydrogens.length !== 2) throw new Error("A molecular orientation must render one O and two H sites");
  const connection = sub(neighborPoint, oxygen);
  const connectionLength = Math.hypot(...connection);
  if (!(connectionLength > 0)) throw new Error("Coincident oxygen anchors cannot define a proton direction");
  const direction = connection.map((value) => value / connectionLength);
  // A learned water orientation donates toward a neighboring oxygen when an
  // O-H vector lies inside a conservative 35-degree cone around the O-O bond.
  // This is a proper-motion-invariant geometric predicate, not an energy or
  // potential. The wide margin tolerates the finite fitted coordinate noise
  // while keeping tetrahedrally distinct directions separate.
  return hydrogens.some((hydrogen) => {
    const oh = sub(hydrogen, oxygen);
    const length = Math.hypot(...oh);
    return length > 0 && dot(oh, direction) / length >= Math.cos(DONOR_CONE_DEGREES * Math.PI / 180);
  });
}

function orientationConstraintAudit(artifact, hypotheses, anchorSites) {
  const records = [...hypotheses.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([key, domain]) => ({ key, point: anchorSites.get(key)[1],
      domain: [...domain.entries()].sort(([first], [second]) => first.localeCompare(second))
        .map(([poseKey, occurrence]) => ({ poseKey, occurrence })) }));
  const edges = [];
  records.forEach((left, first) => records.slice(first + 1).forEach((right, offset) => {
    const second = first + offset + 1;
    const separation = distance(left.point, right.point);
    if (Math.abs(separation - artifact.anchor.connectionDistance) > artifact.anchor.connectionTolerance) return;
    const allowed = left.domain.map((leftPose) => right.domain.map((rightPose) =>
      Number(donorTowardAnchor(artifact, leftPose.occurrence, right.point))
        + Number(donorTowardAnchor(artifact, rightPose.occurrence, left.point)) === 1));
    edges.push({ first, second, separation, allowed });
  }));
  const incident = records.map(() => []);
  edges.forEach((edge, edgeIndex) => {
    incident[edge.first].push({ edgeIndex, other: edge.second, forward: true });
    incident[edge.second].push({ edgeIndex, other: edge.first, forward: false });
  });
  const initialDomains = records.map((record) => record.domain.map((_, index) => index));

  const pairAllowed = (edge, forward, own, other) => forward
    ? edge.allowed[own]?.[other] === true : edge.allowed[other]?.[own] === true;
  const propagate = (domains) => {
    let changed = true;
    while (changed) {
      changed = false;
      for (let index = 0; index < records.length; index++) {
        const next = domains[index].filter((own) => incident[index].every(({ edgeIndex, other, forward }) =>
          domains[other].some((otherValue) => pairAllowed(edges[edgeIndex], forward, own, otherValue))));
        if (!next.length) return false;
        if (next.length !== domains[index].length) {
          domains[index] = next;
          changed = true;
        }
      }
    }
    return true;
  };
  const solveFirst = (sourceDomains) => {
    const domains = sourceDomains.map((domain) => domain.slice());
    if (!propagate(domains)) return null;
    const unresolved = domains.map((domain, index) => ({ index, size: domain.length }))
      .filter(({ size }) => size > 1).sort((left, right) => left.size - right.size || left.index - right.index)[0];
    if (!unresolved) return domains.map((domain) => domain[0]);
    for (const value of domains[unresolved.index]) {
      const branch = domains.map((domain) => domain.slice());
      branch[unresolved.index] = [value];
      const solution = solveFirst(branch);
      if (solution) return solution;
    }
    return null;
  };

  const arcDomains = initialDomains.map((domain) => domain.slice());
  const arcConsistent = propagate(arcDomains);
  const canonical = arcConsistent ? solveFirst(arcDomains) : null;
  const supportedDomains = arcConsistent && canonical ? arcDomains.map((domain, index) =>
    domain.filter((value) => {
      const branch = arcDomains.map((candidate) => candidate.slice());
      branch[index] = [value];
      return Boolean(solveFirst(branch));
    })) : records.map(() => []);
  const consistent = supportedDomains.every((domain) => domain.length > 0);
  const resolvedAnchors = consistent ? supportedDomains.filter((domain) => domain.length === 1).length : 0;
  const canonicalAssignment = consistent ? solveFirst(supportedDomains) : null;
  let constrainedEdgesSatisfied = 0;
  if (canonicalAssignment) edges.forEach((edge) => {
    if (edge.allowed[canonicalAssignment[edge.first]]?.[canonicalAssignment[edge.second]]) constrainedEdgesSatisfied++;
  });
  const uniqueHydrogenSites = consistent ? records.flatMap((record, index) => {
    if (supportedDomains[index].length !== 1) return [];
    const occurrence = record.domain[supportedDomains[index][0]].occurrence;
    return renderSites(artifact, occurrence).filter(([species]) => species === "H");
  }) : [];
  const orientationDomains = records.map((record, index) => ({
    anchorKey: record.key,
    anchorSite: ["O", [...record.point]],
    alternatives: supportedDomains[index].map((value) => {
      const pose = record.domain[value];
      return { poseKey: pose.poseKey,
        sites: renderSites(artifact, pose.occurrence).map(([species, point]) => [species, [...point]]) };
    }),
  }));
  const orientationConstraints = edges.map((edge) => ({
    firstAnchorKey: records[edge.first].key,
    secondAnchorKey: records[edge.second].key,
    separation: edge.separation,
    allowedPosePairs: records[edge.first].domain.flatMap((firstPose, firstIndex) =>
      records[edge.second].domain.flatMap((secondPose, secondIndex) =>
        edge.allowed[firstIndex]?.[secondIndex] && supportedDomains[edge.first].includes(firstIndex)
          && supportedDomains[edge.second].includes(secondIndex)
          ? [[firstPose.poseKey, secondPose.poseKey]] : [])),
  }));
  return {
    schema: "gcts-ice-orientation-constraint-audit-v1",
    anchors: records.length,
    initialHypotheses: initialDomains.reduce((sum, domain) => sum + domain.length, 0),
    globallySupportedHypotheses: supportedDomains.reduce((sum, domain) => sum + domain.length, 0),
    oxygenConnections: edges.length,
    donorConeDegrees: DONOR_CONE_DEGREES,
    donorPredicate: "proper-motion-invariant O-H/O-O direction cosine",
    interiorAnchors: incident.filter((neighbors) => neighbors.length === 4).length,
    boundaryAnchors: incident.filter((neighbors) => neighbors.length < 4).length,
    maximumCoordination: Math.max(0, ...incident.map((neighbors) => neighbors.length)),
    consistent,
    resolvedAnchors,
    ambiguousAnchors: consistent ? records.length - resolvedAnchors : records.length,
    constrainedEdgesSatisfied,
    constrainedEdgesTotal: edges.length,
    uniqueHydrogenSites,
    orientationDomains,
    orientationConstraints,
    allHydrogensResolved: consistent && resolvedAnchors === records.length,
    targetUsed: false,
    physicalPotentialUsed: false,
    canonicalBranchMaterialized: false,
    claimBoundary: "Binary O-O constraints require exactly one geometrically donated proton on every observed scaffold edge. Boundary bonds outside the finite public domain remain open; ambiguous H2O poses stay symbolic, and no energy, entropy, tunnelling, kinetics, probability, or physical time is inferred.",
  };
}

function portOrbit(artifact, port) {
  const orbit = new Map();
  artifact.prototype.properSymmetries.forEach((parentSymmetry) => {
    const translation = matvec(parentSymmetry, port.translation);
    artifact.prototype.properSymmetries.forEach((childSymmetry) => {
      const rotation = matmul(matmul(parentSymmetry, port.rotation), transpose(childSymmetry));
      const key = JSON.stringify([...rotation.flat(), ...translation].map((value) => Math.round(value / 1e-7)));
      orbit.set(key, { rotation, translation });
    });
  });
  return [...orbit.entries()].sort(([first], [second]) => first.localeCompare(second)).map(([, pose]) => pose);
}

export function validateIceMolecularPortArtifact(artifact) {
  if (artifact.schema !== "gcts-ice-molecular-port-artifact-v1") throw new Error("Unknown ice molecular-port artifact schema");
  if (artifact.provenance.targetUsed) throw new Error("Target-tainted molecular grammar cannot execute");
  if (artifact.prototype.sites.length !== 3 || artifact.ports.length !== 8) throw new Error("Incomplete frozen H2O port vocabulary");
  const rotations = [
    ...artifact.prototype.properSymmetries,
    ...artifact.ports.map((port) => port.rotation),
    ...Object.values(artifact.cases).flatMap((item) => item.seedOccurrences.map((occurrence) => occurrence.rotation)),
  ];
  if (rotations.some((rotation) => Math.abs(determinant(rotation) - 1) > 1e-8 || matrixResidual(rotation) > 1e-8)) {
    throw new Error("Frozen molecular artifact contains a non-proper or non-orthonormal pose");
  }
  return true;
}

export function executeIceMolecularAnchorGrowth(artifact, caseId) {
  validateIceMolecularPortArtifact(artifact);
  const config = artifact.cases[caseId];
  if (!config) throw new Error(`No frozen molecular continuation case ${caseId}`);
  const anchorTolerance = .06;
  const poseTolerance = artifact.provenance.poseTolerance;
  const hypotheses = new Map();
  const anchorSites = new Map();
  config.seedOccurrences.forEach((occurrence) => {
    const anchor = anchorSite(artifact, occurrence);
    const anchorKey = quantizedSitesKey([anchor], anchorTolerance);
    const poseKey = quantizedSitesKey(renderSites(artifact, occurrence), poseTolerance);
    const domain = hypotheses.get(anchorKey) || new Map();
    domain.set(poseKey, occurrence);
    hypotheses.set(anchorKey, domain);
    anchorSites.set(anchorKey, anchor);
  });
  const seedKeys = new Set(hypotheses.keys());
  const seedOrientationAudit = orientationConstraintAudit(artifact, hypotheses, anchorSites);
  const waves = [];
  for (let waveIndex = 0; waveIndex < config.maximumWaves; waveIndex++) {
    const proposals = new Map();
    const proposalParents = new Map();
    hypotheses.forEach((alternatives, parentAnchorKey) => alternatives.forEach((parent, parentPoseKey) => {
      artifact.ports.forEach((port) => portOrbit(artifact, port).forEach((relative) => {
        const occurrence = {
          rotation: matmul(parent.rotation, relative.rotation),
          translation: add(parent.translation, matvec(parent.rotation, relative.translation)),
        };
        const anchor = anchorSite(artifact, occurrence);
        const anchorKey = quantizedSitesKey([anchor], anchorTolerance);
        if (hypotheses.has(anchorKey)) return;
        if (distance(anchor[1], config.boundaryCenter) > config.boundaryRadius + anchorTolerance) return;
        if ([...anchorSites.values()].some((existing) => distance(anchor[1], existing[1]) < artifact.anchor.exclusionDistance)) return;
        const poseKey = quantizedSitesKey(renderSites(artifact, occurrence), poseTolerance);
        const alternativesForAnchor = proposals.get(anchorKey) || new Map();
        const prior = alternativesForAnchor.get(poseKey);
        alternativesForAnchor.set(poseKey, { occurrence, support: port.observations + (prior?.support || 0) });
        proposals.set(anchorKey, alternativesForAnchor);
        const parentsForAnchor = proposalParents.get(anchorKey) || new Map();
        const parentPoses = parentsForAnchor.get(parentAnchorKey) || new Set();
        parentPoses.add(parentPoseKey);
        parentsForAnchor.set(parentAnchorKey, parentPoses);
        proposalParents.set(anchorKey, parentsForAnchor);
      }));
    }));

    let rejectedNonunanimous = 0;
    if (config.requireParentDomainUnanimity) {
      [...proposals.keys()].forEach((anchorKey) => {
        const unanimous = [...(proposalParents.get(anchorKey) || new Map()).entries()]
          .some(([parentAnchorKey, parentPoses]) => parentPoses.size === hypotheses.get(parentAnchorKey).size);
        if (!unanimous) { proposals.delete(anchorKey); rejectedNonunanimous++; }
      });
    }
    const accepted = [];
    const acceptedPoints = [];
    [...proposals.keys()].sort().forEach((anchorKey) => {
      const exemplar = proposals.get(anchorKey).values().next().value.occurrence;
      const anchor = anchorSite(artifact, exemplar);
      if (acceptedPoints.some((point) => distance(anchor[1], point) < artifact.anchor.exclusionDistance)) return;
      accepted.push(anchorKey);
      acceptedPoints.push(anchor[1]);
    });
    if (!accepted.length) {
      const orientationAudit = orientationConstraintAudit(artifact, hypotheses, anchorSites);
      waves.push({ wave: waveIndex + 1, candidateAnchors: proposals.size, acceptedAnchors: 0,
        retainedOrientationHypotheses: 0, rejectedNonunanimousAnchors: rejectedNonunanimous,
        rejectedCandidateAnchors: proposals.size,
        emittedAnchors: [], orientationAudit });
      break;
    }
    let retained = 0;
    const emittedAnchors = [];
    accepted.forEach((anchorKey) => {
      const ranked = [...proposals.get(anchorKey).entries()].sort((first, second) =>
        second[1].support - first[1].support || first[0].localeCompare(second[0]))
        .slice(0, config.maximumHypothesesPerAnchor);
      const domain = new Map(ranked.map(([poseKey, record]) => [poseKey, record.occurrence]));
      hypotheses.set(anchorKey, domain);
      retained += domain.size;
      const anchor = anchorSite(artifact, domain.values().next().value);
      anchorSites.set(anchorKey, anchor);
      emittedAnchors.push(anchor);
    });
    const orientationAudit = orientationConstraintAudit(artifact, hypotheses, anchorSites);
    waves.push({ wave: waveIndex + 1, candidateAnchors: proposals.size,
      acceptedAnchors: accepted.length, retainedOrientationHypotheses: retained,
      rejectedNonunanimousAnchors: rejectedNonunanimous,
      rejectedCandidateAnchors: proposals.size - accepted.length, emittedAnchors, orientationAudit });
  }
  const emittedAnchors = [...anchorSites.entries()].filter(([key]) => !seedKeys.has(key)).map(([, site]) => site);
  const actualCounts = waves.map((wave) => wave.acceptedAnchors);
  const orientationAudit = waves.at(-1)?.orientationAudit || seedOrientationAudit;
  return {
    caseId,
    seedAnchors: seedKeys.size,
    seedSites: [...seedKeys].map((key) => anchorSites.get(key)),
    waves,
    emittedAnchors,
    unresolvedOrientationHypotheses: [...hypotheses.entries()].filter(([key, domain]) => !seedKeys.has(key) && domain.size > 1).length,
    seedOrientationAudit,
    orientationAudit,
    fixedPoint: Boolean(waves.length && waves.at(-1).acceptedAnchors === 0),
    expectedCounts: config.expectedAcceptedAnchors,
    exactBackendCountParity: JSON.stringify(actualCounts) === JSON.stringify(config.expectedAcceptedAnchors),
    targetUsed: false,
    alternativesAreMutuallyExclusive: true,
    stationaryOrExponentialClaim: false,
    artifactDigest: artifact.artifactDigest,
    boundaryCenter: config.boundaryCenter.slice(),
    boundaryRadius: config.boundaryRadius,
    portCount: artifact.ports.length,
    conformerTypes: 1,
    moleculeLabel: "H₂O",
    orientationSpecies: "H",
    gapLabel: "O₆",
    selectionRuleLabel: "orientation-domain unanimity",
    fixedPointReason: "No parent orientation domain unanimously supports another non-conflicting oxygen anchor.",
    provenance: { ...artifact.provenance },
  };
}
