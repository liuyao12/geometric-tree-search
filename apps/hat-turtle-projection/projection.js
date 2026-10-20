// Integer coefficients use two triangular bases, not four orthonormal axes.
export const HALFROOT3 = Math.sqrt(3) / 2;
export function latticeToCartesian([p, q, r, s]) {
  return [p + q / 2, HALFROOT3 * q, HALFROOT3 * r, r / 2 + s];
}
export function relativeTile(vertices, ids) {
  const origin = vertices[ids[0]];
  return ids.map(id => vertices[id].map((v, k) => v - origin[k]));
}
export function reflectedFrameStats(centers, labels) {
  const mean = [0, 0, 0, 0];
  let count = 0;
  labels.forEach((label, i) => {
    if (label !== 'H1') return;
    count++;
    for (let k = 0; k < 4; k++) mean[k] += centers[i * 4 + k];
  });
  for (let k = 0; k < 4; k++) mean[k] /= count;
  let uu = 0, vv = 0, uv = 0, nuRe = 0, nuIm = 0;
  let nvRe = 0, nvIm = 0, targetNorm = 0;
  labels.forEach((label, i) => {
    if (label !== 'H1') return;
    const ux = centers[i*4] - mean[0], uy = centers[i*4+1] - mean[1];
    const vx = centers[i*4+2] - mean[2], vy = centers[i*4+3] - mean[3];
    const zx = .5 * ux + HALFROOT3 * vx, zy = .5 * uy + HALFROOT3 * vy;
    uu += ux*ux + uy*uy; vv += vx*vx + vy*vy; uv += ux*vx + uy*vy;
    nuRe += zx*ux + zy*uy; nuIm += zy*ux - zx*uy;
    nvRe += zx*vx + zy*vy; nvIm += zy*vx - zx*vy;
    targetNorm += zx*zx + zy*zy;
  });
  return {mean, count, uu, vv, uv, nuRe, nuIm, nvRe, nvIm, targetNorm};
}
export function steadyFrame(stats, c, s) {
  const denominator = c*c*stats.uu + 2*c*s*stats.uv + s*s*stats.vv;
  const re = (c*stats.nuRe + s*stats.nvRe) / denominator;
  const im = (c*stats.nuIm + s*stats.nvIm) / denominator;
  const [ux, uy, vx, vy] = stats.mean;
  const mx = c*ux + s*vx, my = c*uy + s*vy;
  const tx = .5*ux + HALFROOT3*vx - (re*mx - im*my);
  const ty = .5*uy + HALFROOT3*vy - (im*mx + re*my);
  const residualSquared = Math.max(0, stats.targetNorm - denominator*(re*re + im*im));
  return {re, im, tx, ty, scale: Math.hypot(re, im), rms: Math.sqrt(residualSquared/stats.count)};
}
export const IDENTITY_FRAME = {re:1, im:0, tx:0, ty:0, scale:1, rms:0};
export function projectVertex(u, v, a, b, c, s, lifted, frame=IDENTITY_FRAME) {
  const x = c*u + s*a, y = c*v + s*b;
  const rx = frame.re*x - frame.im*y + frame.tx;
  const ry = frame.im*x + frame.re*y + frame.ty;
  if (!lifted) return [rx, ry, 0];
  const z = (-s*(u+v) + c*(a+b)) / Math.SQRT2 * frame.scale;
  const tilt = .54;
  return [rx, Math.cos(tilt)*ry - Math.sin(tilt)*z, Math.sin(tilt)*ry + Math.cos(tilt)*z];
}
