// Estimate the orientation, not the spacing or an exact lattice, of the marks.
// The sixth harmonic identifies directions differing by sixty degrees.
export function whiteMarkAlignment(points) {
  let real = 0, imaginary = 0, count = 0;
  for (let i = 0; i < points.length; i++) {
    let distance = Infinity, dx = 0, dy = 0;
    for (let j = 0; j < points.length; j++) {
      if (i === j) continue;
      const x = points[j][0] - points[i][0], y = points[j][1] - points[i][1], squared = x * x + y * y;
      if (squared > 0 && squared < distance) { distance = squared; dx = x; dy = y; }
    }
    if (!Number.isFinite(distance)) continue;
    const angle = 6 * Math.atan2(dy, dx);
    real += Math.cos(angle); imaginary += Math.sin(angle); count++;
  }
  const coherence = count ? Math.hypot(real, imaginary) / count : 0;
  const angle = coherence > 1e-12 ? -Math.atan2(imaginary, real) / 6 : 0;
  return {re: Math.cos(angle), im: Math.sin(angle), angle, count, coherence};
}
export function rotateFrame(frame, rotation) {
  const {re, im} = rotation;
  return {...frame,
    re: re * frame.re - im * frame.im, im: im * frame.re + re * frame.im,
    tx: re * frame.tx - im * frame.ty, ty: im * frame.tx + re * frame.ty};
}
