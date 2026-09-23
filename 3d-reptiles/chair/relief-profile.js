// A concrete colored-relief realization of Goodman–Strauss's bumps/nicks
// recipe (Section 2), not a reconstruction of Tsiokos's numbered pyramids.
export function reliefFeatures(color) {
  // Touching bases join the inward slopes into one coplanar blue face.
  if (color === 'blue') return [
    { u: .16, v: .08, radius: .16, height: .12 },
    { u: -.16, v: .08, radius: .16, height: -.12 },
  ];
  return [{ u: 0, v: .10, radius: .24, height: color === 'red' ? .12 : -.12 }];
}

export function reliefFrame(mark) {
  const n = mark.direction;
  const length = Math.hypot(...mark.arrow);
  const forward = mark.arrow.map(value => value / length);
  const side = [forward[1] * n[2] - forward[2] * n[1],
    forward[2] * n[0] - forward[0] * n[2], forward[0] * n[1] - forward[1] * n[0]];
  const center = mark.cell.map((value, i) => value + .5 + .5 * n[i]);
  return { center, side, forward, normal: n };
}

export function reliefPoint(frame, u, v, height = 0) {
  return frame.center.map((value, i) => value + u * frame.side[i] + v * frame.forward[i] + height * frame.normal[i]);
}

export function reliefHeight(mark, point) {
  const frame = reliefFrame(mark);
  const relative = point.map((value, i) => value - frame.center[i]);
  const dot = vector => relative.reduce((sum, value, i) => sum + value * vector[i], 0);
  const u = dot(frame.side), v = dot(frame.forward);
  return reliefFeatures(mark.color).reduce((sum, feature) => sum + feature.height * Math.max(0,
    1 - Math.max(Math.abs(u - feature.u), Math.abs(v - feature.v)) / feature.radius), 0);
}
