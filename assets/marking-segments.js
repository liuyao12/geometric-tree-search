// Each component follows a primitive A₂ lattice direction. Centered half-steps
// meet the corresponding segment at the next lattice point in that direction.
export function markingSegmentEndpoints({point, component}) {
  return segmentEndpoints(point, component, 0.5);
}

// Leave a visible gap between consecutive equal signs on a Turtle stripe.
export function shortMarkingSegmentEndpoints({point, component}) {
  return segmentEndpoints(point, component, 0.32);
}

function segmentEndpoints(point, component, halfLength) {
  const direction = [1, 1, 1];
  direction[component] = -2;
  return [-halfLength, halfLength].map(t => point.map((value, i) => value + t * direction[i]));
}
