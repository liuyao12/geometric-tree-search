const EPSILON = 1e-10;

const clamp = (value, lower, upper) => Math.max(lower, Math.min(upper, value));
const subtract = (first, second) => first.map((value, axis) => value - second[axis]);
const dot = (first, second) => first.reduce((sum, value, axis) => sum + value * second[axis], 0);
const cross = (first, second) => [
  first[1] * second[2] - first[2] * second[1],
  first[2] * second[0] - first[0] * second[2],
  first[0] * second[1] - first[1] * second[0],
];
const norm = (vector) => Math.sqrt(dot(vector, vector));
const normalize = (vector) => {
  const length = norm(vector);
  return length > EPSILON ? vector.map((value) => value / length) : null;
};

function median(values) {
  if (!values.length) return 0;
  const ordered = values.slice().sort((first, second) => first - second);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : .5 * (ordered[middle - 1] + ordered[middle]);
}
function validateOccurrence(occurrence, expectedSize = null) {
  if (!occurrence || !Array.isArray(occurrence.species) || !Array.isArray(occurrence.positions)
    || occurrence.species.length !== occurrence.positions.length || !occurrence.species.length) {
    throw new Error("pose occurrence requires equally sized, nonempty species and positions");
  }
  if (expectedSize !== null && occurrence.species.length !== expectedSize) {
    throw new Error("pose occurrences must have fixed topology");
  }
  occurrence.positions.forEach((position) => {
    if (!Array.isArray(position) || position.length !== 3 || position.some((value) => !Number.isFinite(value))) {
      throw new Error("pose positions must be finite Cartesian triples");
    }
  });
}

function occurrenceGeometry(occurrence, toleranceFraction) {
  const count = occurrence.positions.length;
  const centroid = [0, 1, 2].map((axis) => occurrence.positions.reduce(
    (sum, position) => sum + position[axis], 0) / count);
  const centered = occurrence.positions.map((position) => subtract(position, centroid));
  const distances = Array.from({ length: count }, () => new Array(count).fill(0));
  const nonzero = [];
  for (let first = 0; first < count; first++) for (let second = first + 1; second < count; second++) {
    const distance = norm(subtract(centered[first], centered[second]));
    distances[first][second] = distances[second][first] = distance;
    if (distance > EPSILON) nonzero.push(distance);
  }
  const scale = median(nonzero) || 1;
  const quantum = Math.max(scale * toleranceFraction, EPSILON);
  const fingerprints = occurrence.species.map((species, site) => `${species}|${occurrence.species
    .map((other, index) => index === site ? null : `${other}:${Math.round(distances[site][index] / quantum)}`)
    .filter(Boolean).sort().join(",")}`);
  return { centered, distances, fingerprints, scale, quantum };
}

function intrinsicFrames(occurrence, toleranceFraction) {
  const geometry = occurrenceGeometry(occurrence, toleranceFraction);
  const frames = [];
  for (let first = 0; first < geometry.centered.length; first++) {
    const x = normalize(geometry.centered[first]);
    if (!x) continue;
    for (let second = 0; second < geometry.centered.length; second++) {
      if (first === second) continue;
      const normal = normalize(cross(geometry.centered[first], geometry.centered[second]));
      if (!normal || norm(cross(geometry.centered[first], geometry.centered[second])) < geometry.scale ** 2 * .02) continue;
      const y = normalize(cross(normal, x));
      if (!y) continue;
      const key = [
        geometry.fingerprints[first], geometry.fingerprints[second],
        Math.round(norm(geometry.centered[first]) / geometry.quantum),
        Math.round(norm(geometry.centered[second]) / geometry.quantum),
        Math.round(dot(geometry.centered[first], geometry.centered[second]) / geometry.quantum ** 2),
      ].join("|");
      // Columns form a right-handed intrinsic frame in laboratory coordinates.
      frames.push({ key, axes: [x, y, normal] });
    }
  }
  if (!frames.length) return { frames: [], geometry };
  const canonicalKey = frames.reduce((best, frame) => best === null || frame.key < best ? frame.key : best, null);
  return { frames: frames.filter((frame) => frame.key === canonicalKey), geometry };
}

function frameAngle(first, second) {
  const trace = first.axes.reduce((sum, axis, index) => sum + dot(axis, second.axes[index]), 0);
  return Math.acos(clamp((trace - 1) / 2, -1, 1));
}

function frameOrbitDistance(first, second) {
  if (!first.frames.length || !second.frames.length) return Infinity;
  let best = Infinity;
  first.frames.forEach((firstFrame) => second.frames.forEach((secondFrame) => {
    best = Math.min(best, frameAngle(firstFrame, secondFrame));
  }));
  return best;
}

function canonicalAxis(frame) {
  const { geometry } = frame;
  let best = null;
  for (let first = 0; first < geometry.centered.length; first++) for (let second = first + 1; second < geometry.centered.length; second++) {
    const raw = subtract(geometry.centered[second], geometry.centered[first]);
    const length = norm(raw);
    if (length <= EPSILON) continue;
    const ordered = geometry.fingerprints[first].localeCompare(geometry.fingerprints[second]);
    const directed = ordered < 0 ? raw : ordered > 0 ? raw.map((value) => -value) : raw;
    const key = [
      [geometry.fingerprints[first], geometry.fingerprints[second]].sort().join("<>"),
      Math.round(length / geometry.quantum),
    ].join("|");
    if (!best || key < best.key || key === best.key && length > best.length) {
      best = { key, length, axis: normalize(directed), unoriented: ordered === 0 };
    }
  }
  return best;
}

function axialDistance(first, second) {
  if (!first || !second || first.key !== second.key) return Infinity;
  const cosine = clamp(dot(first.axis, second.axis), -1, 1);
  const angle = Math.acos(cosine);
  return first.unoriented || second.unoriented ? Math.min(angle, Math.PI - angle) : angle;
}

/**
 * Classify observed cluster poses modulo each colored cluster's proper symmetry.
 * The result is invariant to global translation and equivariant to a common
 * proper rotation. It does not infer a physical potential or invent unobserved
 * orientations; it only quotients the supplied occurrences.
 */
export function classifyProperPoseOrbits(occurrences, {
  metricToleranceFraction = .025,
  angularToleranceRadians = .12,
} = {}) {
  if (!Array.isArray(occurrences) || !occurrences.length) return {
    orientations: 0, assignments: [], populations: [], support: "unavailable",
    properSymmetryGaugeCount: 0, frameKind: "none",
  };
  occurrences.forEach((occurrence) => validateOccurrence(occurrence, occurrences[0].species.length));
  const frames = occurrences.map((occurrence) => intrinsicFrames(occurrence, metricToleranceFraction));
  const hasProperFrames = frames.every((frame) => frame.frames.length > 0);
  const axes = hasProperFrames ? [] : frames.map(canonicalAxis);
  const frameKind = hasProperFrames ? "right-handed intrinsic frame"
    : axes.every(Boolean) ? "axial stabilizer" : "orientation-invisible support";
  const representatives = [];
  const assignments = [];
  const populations = [];
  frames.forEach((frame, occurrenceIndex) => {
    let orbit = representatives.findIndex((representativeIndex) => {
      const distance = hasProperFrames
        ? frameOrbitDistance(frame, frames[representativeIndex])
        : axes[occurrenceIndex] && axes[representativeIndex]
          ? axialDistance(axes[occurrenceIndex], axes[representativeIndex]) : 0;
      return distance <= angularToleranceRadians;
    });
    if (orbit < 0) {
      orbit = representatives.length;
      representatives.push(occurrenceIndex);
      populations.push(0);
    }
    assignments.push(orbit);
    populations[orbit]++;
  });
  const everyPoseRepeated = populations.length > 0 && populations.every((population) => population >= 2);
  const sampledFraction = representatives.length / occurrences.length;
  const support = frameKind === "orientation-invisible support" ? "finite required set"
    : occurrences.length >= 12 && sampledFraction >= .8
      ? (frameKind === "axial stabilizer" ? "sampled axial continuum" : "sampled continuum")
      : everyPoseRepeated ? "finite required set" : "unresolved support";
  return {
    orientations: representatives.length,
    assignments,
    populations: populations.slice().sort((first, second) => second - first),
    support,
    properSymmetryGaugeCount: hasProperFrames ? Math.max(...frames.map((frame) => frame.frames.length)) : 0,
    frameKind,
    metricToleranceFraction,
    angularToleranceRadians,
    globalTranslationInvariant: true,
    commonProperRotationEquivariant: true,
    improperRotationsQuotiented: false,
  };
}
