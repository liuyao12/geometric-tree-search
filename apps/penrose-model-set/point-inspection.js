import { canonical, embedding, latticeKey } from '../../assets/cyclotomic-five.js';
import { ammannStates } from '../../assets/penrose-ammann.js?v=20260907-extent';

import { extendBar, markingValue } from "../../assets/penrose-extensions.js?v=20260907-extent";

export function formatCyclotomic(point) {
  const { coeff, denominator } = canonical(point), basis = ['', 'ζ₅', 'ζ₅²', 'ζ₅³'];
  const terms = [];
  coeff.forEach((n, i) => {
    if (!n) return;
    const body = `${i && Math.abs(n) === 1 ? '' : Math.abs(n)}${basis[i]}`;
    terms.push(`${terms.length ? n < 0 ? ' − ' : ' + ' : n < 0 ? '−' : ''}${body}`);
  });
  const numerator = terms.join('') || '0';
  return denominator === 1 ? numerator : `(${numerator}) / ${denominator}`;
}
export function fraction(n, d = 10) {
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  const g = gcd(Math.abs(n), d); n /= g; d /= g;
  return d === 1 ? String(n) : `${n}/${d}`;
}

// Exact sample locations; m is evaluated lazily only at the hovered point.
export function inspectionPoints(snapshot) {
  const points = new Map(), orientations = new Map(snapshot.orientations), context = [], extent = snapshot.extent || 0;
  const at = point => {
    const key = latticeKey(point);
    if (!points.has(key)) {
      const item = { key, exact: canonical(point), position: embedding(point), vertex: false, extension: false, t: 0, contributions: new Map() };
      let values;
      Object.defineProperty(item, 'markings', { get() {
        if (!values) values = new Map(context.flatMap(({ tile, state, label }) => {
          const value = markingValue(tile, state, item.exact, extent);
          return value ? [[tile.id, { label, value }]] : [];
        }));
        return values;
      }});
      points.set(key, item);
    }
    return points.get(key);
  };
  snapshot.tiles.forEach((tile, index) => {
    const label = `${tile.kind} #${index + 1}`;
    tile.exactPoints.forEach((point, k) => {
      const item = at(point); item.vertex = true; item.t += tile.weights[k];
      item.contributions.set(tile.id, { label, weight: tile.weights[k] });
    });
    const states = ammannStates(tile), state = states.find(s => s.start === orientations.get(tile.id)) || states[0];
    context.push({ tile, state, label });
    for (const bar of state.bars) {
      for (const end of bar.ends) at(end.point);
      if (extent) {
        const extended = extendBar(bar, extent);
        at(extended.from).extension = true; at(extended.to).extension = true;
      }
    }
  });
  return [...points.values()];
}
const vector = value => value.map(v => v === null ? '—' : v).join(', ');
export function inspectionText(point, useMarkings) {
  const values = [...point.markings.values()], merged = [null, null, null, null, null];
  let mismatch = false;
  for (const { value } of values) value.forEach((v, i) => {
    if (v === null) return;
    if (merged[i] !== null && merged[i] !== v) mismatch = true;
    merged[i] = v;
  });
  const tParts = [...point.contributions.values()].map(c => `${c.label}: ${fraction(c.weight)}`);
  return {
    title: point.vertex ? 'Tile vertex' : point.extension ? 'Extension endpoint' : 'Ammann endpoint',
    coordinate: `x = ${formatCyclotomic(point.exact)}`,
    basis: `Basis coefficients: (${point.exact.coeff.join(', ')})${point.exact.denominator === 1 ? '' : ` / ${point.exact.denominator}`}`,
    t: `t(x) = ${fraction(point.t)}${tParts.length > 1 ? ` = ${tParts.map(p => p.split(': ')[1]).join(' + ')}` : tParts.length ? '' : ' · outside vertex support'}`,
    m: !values.length ? 'm(x) = undefined · outside marking support'
      : mismatch ? `m(x): mismatch · ${values.map(v => `(${vector(v.value)})`).join(' ≠ ')}`
      : `m(x) = (${vector(merged)}) · ${values.length} tile support${values.length === 1 ? '' : 's'} compatible`,
    detail: `${tParts.join(' · ')}${tParts.length ? '\n' : ''}${values.map(v => `${v.label}: m = (${vector(v.value)})`).join(' · ')}${values.length ? '\n' : ''}1 = bar, 0 = off bar inside tile, — = outside component support.\n${useMarkings ? 'Ammann matching enforced' : 'Ammann values shown; search checks edge arrows'}`
  };
}
