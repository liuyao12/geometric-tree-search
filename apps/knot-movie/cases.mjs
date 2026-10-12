import { parse, canonical } from './engine.mjs';

// Close a braid by following each strand to its top endpoint. No move sequence
// is supplied to the knot search: these are independently specified endpoints.
export function braidClosure(generators, strands) {
  if (!Number.isInteger(strands) || strands < 2 || strands > 16 ||
      generators.some(g => !Number.isInteger(g) || !g || Math.abs(g) >= strands)) throw Error('Invalid braid.');
  const positions = Array.from({ length: strands }, (_, i) => i);
  const events = positions.map(() => []);
  generators.forEach((g, k) => {
    const i = Math.abs(g) - 1, a = positions[i], b = positions[i + 1];
    events[a].push({ id: k + 1, over: g > 0, sign: Math.sign(g) });
    events[b].push({ id: k + 1, over: g < 0, sign: Math.sign(g) });
    [positions[i], positions[i + 1]] = [b, a];
  });
  const visited = new Set(), word = []; let strand = 0;
  do {
    visited.add(strand); word.push(...events[strand]);
    strand = positions.indexOf(strand);
  } while (strand !== 0);
  if (visited.size !== strands) throw Error('Braid closure has multiple components.');
  return canonical(parse(canonical(word)));
}

export const trefoilIdentification = Object.freeze({
  name: 'Six-crossing trefoil → standard trefoil',
  source: braidClosure([1, 1, 2, 1, 2, -1], 3),
  target: braidClosure([1, 1, 1], 2),
  depth: 3, crossingCap: 6,
});
