import { canonical, embedding, latticeKey } from '../../assets/cyclotomic-five.js';
import { ammannStates } from '../../assets/penrose-ammann.js?v=20260907-arrows';

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

// Inspect the implemented finite supports, not an invented continuous field:
// t is the stored vertex/corner weight divided by ten. m at a decoration port
// is the five-vector counting stripe ends by family. Matching glues m values;
// it does not sum them. At other points m is outside its finite support.
export function inspectionPoints(snapshot) {
  const points = new Map(), orientations = new Map(snapshot.orientations);
  const at = point => {
    const key = latticeKey(point);
    if (!points.has(key)) points.set(key, { key, exact: canonical(point), position: embedding(point), vertex: false, t: 0, contributions: new Map(), markings: new Map() });
    return points.get(key);
  };
  snapshot.tiles.forEach((tile, index) => {
    const label = `${tile.kind} #${index + 1}`;
    tile.exactPoints.forEach((point, k) => {
      const item = at(point); item.vertex = true; item.t += tile.weights[k];
      item.contributions.set(tile.id, { label, weight: tile.weights[k] });
    });
    const states = ammannStates(tile), state = states.find(s => s.start === orientations.get(tile.id)) || states[0];
    for (const bar of state.bars) for (const end of bar.ends) {
      const item = at(end.point);
      if (!item.markings.has(tile.id)) item.markings.set(tile.id, { label, value: [0, 0, 0, 0, 0] });
      item.markings.get(tile.id).value[bar.family]++;
    }
  });
  return [...points.values()];
}

export function inspectionText(point, useMarkings) {
  const values = [...point.markings.values()];
  const unique = new Set(values.map(m => m.value.join(', ')));
  const tParts = [...point.contributions.values()].map(c => `${c.label}: ${fraction(c.weight)}`);
  return {
    title: point.vertex ? 'Tile vertex' : 'Ammann endpoint',
    coordinate: `x = ${formatCyclotomic(point.exact)}`,
    basis: `Basis coefficients: (${point.exact.coeff.join(', ')})${point.exact.denominator === 1 ? '' : ` / ${point.exact.denominator}`}`,
    t: `t(x) = ${fraction(point.t)}${tParts.length > 1 ? ` = ${tParts.map(p => p.split(': ')[1]).join(' + ')}` : tParts.length ? '' : ' · outside vertex support'}`,
    m: unique.size === 0 ? 'm(x) = undefined · outside marking support'
      : unique.size === 1 ? `m(x) = (${[...unique][0]}) · ${values.length} tile${values.length === 1 ? '' : 's'} agree`
      : `m(x): mismatch · ${[...unique].map(v => `(${v})`).join(' ≠ ')}`,
    detail: `${tParts.join(' · ')}${tParts.length ? '\n' : ''}${values.map(v => `${v.label}: m = (${v.value.join(', ')})`).join(' · ')}${values.length ? '\n' : ''}${useMarkings ? 'Ammann matching enforced' : 'Ammann values shown; search checks edge arrows'}`
  };
}
