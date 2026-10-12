import { topology, canonical } from './engine.mjs';
const sub = (a, b) => a.map((x, i) => x - b[i]);
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const cross2 = (a, b) => a[0] * b[1] - a[1] * b[0];
export function latticeLoop(input) {
  if (!Array.isArray(input) || input.length < 4 || input.length > 10000) throw Error('Supply a closed lattice loop with 4–10000 vertices.');
  const points = input.map(p => {
    if (!Array.isArray(p) || p.length !== 3 || p.some(x => !Number.isSafeInteger(x) || Math.abs(x) > 1000)) throw Error('Vertices need three integer coordinates of magnitude at most 1000.');
    return [...p];
  });
  if (JSON.stringify(points[0]) === JSON.stringify(points.at(-1))) points.pop();
  const unit = [];
  for (let i = 0; i < points.length; i++) {
    const a = points[i], b = points[(i + 1) % points.length], d = sub(b, a), axes = d.map((x, j) => x ? j : -1).filter(x => x >= 0);
    if (axes.length !== 1) throw Error('Each edge must be nonzero and parallel to one coordinate axis.');
    const axis = axes[0];
    for (let k = 0; k < Math.abs(d[axis]); k++) { const p = [...a]; p[axis] += k * Math.sign(d[axis]); unit.push(p); if (unit.length > 2000) throw Error('Loop exceeds the 2000-unit-edge limit.'); }
  }
  if (new Set(unit.map(p => p.join(','))).size !== unit.length) throw Error('The lattice loop intersects itself.');
  if (unit.length < 4) throw Error('Degenerate loop.');
  return unit;
}
// Integer basis and integer determinants. Direction is perturbed only for a regular diagram.
export function project(points, direction = [1, 1, 1]) {
  const [a, b, c] = direction, u = [b, -a, 0], v = [a * c, b * c, -a * a - b * b];
  const xy = points.map(p => [dot(p, u), dot(p, v)]), depths = points.map(p => dot(p, direction)), crossings = [], n = points.length;
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    if (j === i + 1 || (i === 0 && j === n - 1)) continue;
    const r = sub(xy[(i + 1) % n], xy[i]), s = sub(xy[(j + 1) % n], xy[j]), q = sub(xy[j], xy[i]);
    let den = cross2(r, s), tn = cross2(q, s), un = cross2(q, r);
    if (!den) {
      if (!cross2(q, r)) {
        const k = r[0] ? 0 : 1, lo = Math.max(Math.min(xy[i][k], xy[(i + 1) % n][k]), Math.min(xy[j][k], xy[(j + 1) % n][k]));
        const hi = Math.min(Math.max(xy[i][k], xy[(i + 1) % n][k]), Math.max(xy[j][k], xy[(j + 1) % n][k]));
        if (lo <= hi) throw Error('Projection has overlapping strands; perturb the viewing direction.');
      }
      continue;
    }
    if (den < 0) { den = -den; tn = -tn; un = -un; }
    if (tn < 0 || tn > den || un < 0 || un > den) continue;
    if (!tn || tn === den || !un || un === den) throw Error('Projection crossing is at a lattice vertex; perturb the viewing direction.');
    const height = (depths[i] - depths[j]) * den + (depths[(i + 1) % n] - depths[i]) * tn - (depths[(j + 1) % n] - depths[j]) * un;
    if (!height) throw Error('Spatial self-intersection.');
    const iOver = height > 0, sign = Math.sign(cross2(iOver ? r : s, iOver ? s : r));
    crossings.push({ id: crossings.length + 1, i, j, tn, un, den, iOver, sign,
      xy: [xy[i][0] + r[0] * tn / den, xy[i][1] + r[1] * tn / den] });
  }
  // Reject coincident crossings (including triples) by exact rational comparisons.
  const rats = crossings.map(x => {
    const r = sub(xy[(x.i + 1) % n], xy[x.i]);
    return [BigInt(xy[x.i][0]) * BigInt(x.den) + BigInt(r[0]) * BigInt(x.tn), BigInt(xy[x.i][1]) * BigInt(x.den) + BigInt(r[1]) * BigInt(x.tn), BigInt(x.den)];
  });
  for (let i = 0; i < rats.length; i++) for (let j = 0; j < i; j++) if (rats[i][0] * rats[j][2] === rats[j][0] * rats[i][2] && rats[i][1] * rats[j][2] === rats[j][1] * rats[i][2]) throw Error('Projection has a multiple crossing; perturb the viewing direction.');
  const events = crossings.flatMap(x => [{ id: x.id, over: x.iOver, sign: x.sign, numerator: x.i * x.den + x.tn, denominator: x.den }, { id: x.id, over: !x.iOver, sign: x.sign, numerator: x.j * x.den + x.un, denominator: x.den }]).sort((a, b) => {
    const delta = BigInt(a.numerator) * BigInt(b.denominator) - BigInt(b.numerator) * BigInt(a.denominator);
    return delta < 0n ? -1 : delta > 0n ? 1 : 0;
  });
  const word = events.map(({ id, over, sign }) => ({ id, over, sign })); topology(word);
  return { direction, xy, crossings, word, canonical: canonical(word) };
}
export function regularProjection(points) {
  for (const direction of [[1, 1, 1], [11, 13, 17], [17, 19, 23], [23, 29, 31], [31, 37, 41]]) {
    try { return project(points, direction); } catch { /* a finite set of bad directions */ }
  }
  throw Error('No regular projection among the pilot directions.');
}
export function gridLoop(x, o) {
  const n = x.length;
  if (o.length !== n || new Set(x).size !== n || new Set(o).size !== n || [...x, ...o].some(k => !Number.isInteger(k) || k < 0 || k >= n) || x.some((k, i) => k === o[i])) throw Error('Invalid grid diagram.');
  // Horizontal strands at height zero; vertical strands at height one.
  const points = [], rows = new Set(); let row = 0;
  do {
    if (rows.has(row)) throw Error('Grid has multiple link components.'); rows.add(row);
    const col = x[row], nextRow = o.indexOf(col);
    for (const p of [[o[row], row, 0], [col, row, 0], [col, row, 1], [col, nextRow, 1], [col, nextRow, 0]])
      if (JSON.stringify(p) !== JSON.stringify(points.at(-1))) points.push(p);
    row = nextRow;
  } while (row !== 0);
  if (rows.size !== n) throw Error('Grid has multiple link components.');
  return latticeLoop(points);
}
