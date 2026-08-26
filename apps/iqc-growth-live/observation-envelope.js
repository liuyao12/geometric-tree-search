const finitePoint = (point) => Array.isArray(point) && point.length === 3
  && point.every(Number.isFinite);

const boundsFor = (points) => {
  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  points.forEach((point) => point.forEach((value, axis) => {
    minimum[axis] = Math.min(minimum[axis], value);
    maximum[axis] = Math.max(maximum[axis], value);
  }));
  return { minimum, maximum };
};

const distance = (first, second) => Math.hypot(
  first[0] - second[0], first[1] - second[1], first[2] - second[2]);

export function fitObservationEnvelope(rawPoints, options = {}) {
  const points = rawPoints.filter(finitePoint);
  if (!points.length) return Object.freeze({
    shape: "empty", source: "no observation", center: Object.freeze([0, 0, 0]),
    padding: 0, characteristicReach: 0,
  });
  const padding = Math.max(0, Number(options.padding) || 0);
  const bounds = boundsFor(points);
  const empiricalCenter = bounds.minimum.map((value, axis) => (value + bounds.maximum[axis]) / 2);
  const shape = ["box", "sphere", "slab"].includes(options.shape) ? options.shape : "box";
  const center = finitePoint(options.center) ? [...options.center] : empiricalCenter;
  if (shape === "sphere") {
    const declared = Number(options.radius);
    const radius = Number.isFinite(declared) && declared > 0
      ? declared : Math.max(...points.map((point) => distance(point, center))) + padding;
    return Object.freeze({
      shape, source: Number.isFinite(declared) && declared > 0 ? "declared spherical crop" : "empirical radial envelope",
      center: Object.freeze(center), radius, padding,
      characteristicReach: radius,
    });
  }
  if (shape === "slab") {
    const planarRadius = Math.max(...points.map((point) => Math.hypot(point[0] - center[0], point[1] - center[1]))) + padding;
    const halfThickness = Math.max(padding, (bounds.maximum[2] - bounds.minimum[2]) / 2 + padding);
    return Object.freeze({
      shape, source: "empirical finite slab envelope", center: Object.freeze(center),
      planarRadius, halfThickness, padding, characteristicReach: planarRadius,
    });
  }
  const halfExtents = bounds.minimum.map((value, axis) => (bounds.maximum[axis] - value) / 2 + padding);
  return Object.freeze({
    shape: "box", source: options.source || "empirical finite box envelope",
    center: Object.freeze(center), halfExtents: Object.freeze(halfExtents), padding,
    characteristicReach: Math.min(...halfExtents),
  });
}

export function observationEnvelopeSignedMargin(envelope, point) {
  if (!finitePoint(point) || !envelope || envelope.shape === "empty") return -Infinity;
  const relative = point.map((value, axis) => value - envelope.center[axis]);
  if (envelope.shape === "sphere") return envelope.radius - Math.hypot(...relative);
  if (envelope.shape === "slab") return Math.min(
    envelope.planarRadius - Math.hypot(relative[0], relative[1]),
    envelope.halfThickness - Math.abs(relative[2]),
  );
  return Math.min(...relative.map((value, axis) => envelope.halfExtents[axis] - Math.abs(value)));
}

export function classifyObservationSites(sites, envelope, tolerance = 0) {
  let known = 0;
  let novelInside = 0;
  let beyond = 0;
  let minimumMargin = Infinity;
  let maximumExcursion = 0;
  sites.forEach((site) => {
    if (site.known) { known++; return; }
    const margin = observationEnvelopeSignedMargin(envelope, site.position);
    minimumMargin = Math.min(minimumMargin, margin);
    if (margin >= -Math.max(0, tolerance)) novelInside++;
    else { beyond++; maximumExcursion = Math.max(maximumExcursion, -margin); }
  });
  return Object.freeze({
    known, novel: novelInside + beyond, novelInside, beyond,
    minimumNovelMargin: Number.isFinite(minimumMargin) ? minimumMargin : null,
    maximumExcursion,
  });
}
