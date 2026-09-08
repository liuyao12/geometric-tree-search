import {learnedSupport} from '../../assets/penrose-online-markings.js';
import { canonical, embedding, latticeKey } from '../../assets/cyclotomic-five.js';
import { tileStates, tileMarkingValue } from '../../assets/penrose-mixed-markings.js?v=20260907-frontier';



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

// Only placed support points and contacts induced by current candidates.
export function inspectionPoints(snapshot, { contacts = null, integersOnly = false } = {}) {
  const points = new Map(), orientations = new Map(snapshot.orientations), context = [], extent = snapshot.extent || 0;
  const at = point => {
    const key = latticeKey(point);
    if (!points.has(key)) {
      const item = { key, exact: canonical(point), position: embedding(point), vertex: false, extension: false, intermediate: false, t: 0, contributions: new Map() };
      let values;
      Object.defineProperty(item, 'markings', { get() {
        if (!values) values = new Map(context.flatMap(({ tile, state, label, support }) => {
          const value = snapshot.learning ? support.get(item.key)?.value : tileMarkingValue(tile, state, item.exact, extent);
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
    const states = tileStates(tile), state = states.find(s => s.start === orientations.get(tile.id)) || states[0];
    const support=snapshot.learning?learnedSupport(tile,snapshot.learning.templates[tile.kind]||[]):null;
    context.push({ tile, state, label, support });
    if(support){for(const p of support.values()){const item=at(p.point);item.extension ||= p.extension;item.learned=true;}}
    else for (const bar of state.bars) {
      for (const end of bar.ends) at(end.point);
    }
  });
  for (const contact of contacts?.points || []) {
    const item=at(contact.point);item.extension ||= contact.extension;
    item.candidateContacts=contact.records.map(r=>({...r,...contacts.candidates[r.candidate]}));
    item.conflict=item.candidateContacts.some(r=>r.value!==(r.placedValue??1));
  }
  return [...points.values()].filter(p=>!integersOnly || p.exact.denominator===1);
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
    title: point.vertex ? 'Tile vertex' : point.candidateContacts ? (point.conflict ? 'Candidate conflict witness' : 'Candidate contact') : point.learned ? 'Learned marking point' : 'Ammann endpoint',
    coordinate: `x = ${formatCyclotomic(point.exact)}`,
    basis: `Basis coefficients: (${point.exact.coeff.join(', ')})${point.exact.denominator === 1 ? '' : ` / ${point.exact.denominator}`}`,
    t: `t(x) = ${fraction(point.t)}${tParts.length > 1 ? ` = ${tParts.map(p => p.split(': ')[1]).join(' + ')}` : tParts.length ? '' : ' · outside vertex support'}`,
    m: !values.length ? 'm(x) = undefined · outside marking support'
      : mismatch ? `m(x): mismatch · ${values.map(v => `(${vector(v.value)})`).join(' ≠ ')}`
      : `m(x) = (${vector(merged)}) · ${values.length} tile support${values.length === 1 ? '' : 's'} compatible`,
    detail: `${(point.candidateContacts || []).map(r=>`${r.kind} candidate #${r.candidate+1}: m${r.family+1}(x) = ${r.value} ${r.value!==(r.placedValue??1)?'≠':'='} ${r.placedValue??1} on placed tile; ${r.legal?'currently legal':'currently rejected'}${r.weight?`; adds t = ${fraction(r.weight)}`:''}`).join('\n')}${point.candidateContacts?'\n':''}${tParts.join(' · ')}${tParts.length ? '\n' : ''}${values.map(v => `${v.label}: m = (${vector(v.value)})`).join(' · ')}${values.length ? '\n' : ''}1 = bar, 0 = exclusion, — = undefined component.\n${useMarkings ? 'Learned points filter candidates; precise bars teach unresolved pairs' : 'Ammann values shown; search checks edge decorations'}`
  };
}
