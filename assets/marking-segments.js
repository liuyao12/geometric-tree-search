// Each component follows a primitive A₂ lattice direction. Centered half-steps
// meet the corresponding segment at the next lattice point in that direction.
export function markingSegmentEndpoints({point, component}) {
  const direction = [1, 1, 1];
  direction[component] = -2;
  return [-.5, .5].map(t => point.map((value, i) => value + t * direction[i]));
}
