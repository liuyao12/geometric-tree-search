// Illustration only: this module is never imported by a search or learner.
// Classical two-colour P2 arcs. Lengths are measured from the tile outline,
// so translations, rotations, reflections and reversed vertex order agree.
export const ARC_COLORS = Object.freeze({long: '#b42348', short: '#126d55'});
const TAU = 2 * Math.PI, PHI = (1 + Math.sqrt(5)) / 2;
const mod = a => ((a % TAU) + TAU) % TAU;
export function circularArcs(kind, loop) {
  if (!['kite', 'dart'].includes(kind) || loop.length !== 4) return [];
  const lengths = loop.map((p, i) => Math.hypot(p.x - loop[(i + 1) % 4].x, p.y - loop[(i + 1) % 4].y));
  const unit = Math.min(...lengths), long = unit * PHI;
  const tip = lengths.findIndex((length, i) => Math.abs(length - long) < unit * 1e-7 && Math.abs(lengths[(i + 3) % 4] - long) < unit * 1e-7);
  if (!(unit > 0) || tip < 0) return [];
  const area = loop.reduce((s, p, i) => s + p.x * loop[(i + 1) % 4].y - p.y * loop[(i + 1) % 4].x, 0);
  const sign = Math.sign(area);
  return [
    {vertex: tip, family: 'long', radius: unit * (kind === 'kite' ? 1 : 1 / PHI)},
    {vertex: (tip + 2) % 4, family: 'short', radius: unit * (kind === 'kite' ? 1 / PHI : 1 / PHI ** 2)},
  ].map(arc => {
    const i = arc.vertex, centre = loop[i], next = loop[(i + 1) % 4], prev = loop[(i + 3) % 4];
    const start = Math.atan2(next.y - centre.y, next.x - centre.x);
    const end = Math.atan2(prev.y - centre.y, prev.x - centre.x);
    const sweep = sign * mod(sign * (end - start));
    const at = angle => ({x: centre.x + arc.radius * Math.cos(angle), y: centre.y + arc.radius * Math.sin(angle)});
    return {...arc, centre, start, sweep, from: at(start), to: at(start + sweep), color: ARC_COLORS[arc.family], edges: [i, (i + 3) % 4]};
  });
}

// project uses the page's usual upward world y / downward canvas y convention.
export function drawCircularArcs(ctx, arcs, project, scale, width = 2) {
  ctx.save();
  ctx.lineWidth = width;
  ctx.lineCap = 'round';
  for (const arc of arcs) {
    const c = project(arc.centre);
    ctx.beginPath();
    ctx.arc(c.x, c.y, arc.radius * scale, -arc.start, -(arc.start + arc.sweep), arc.sweep > 0);
    ctx.strokeStyle = arc.color;
    ctx.stroke();
  }
  ctx.restore();
}
