import { distance, register } from "./geometry.mjs";

// A finite observed-only relation on decorated, overlapping supports. This is
// a geometric GCTS constraint plug-in, not scalar occupancy fitting and not a
// completeness claim over continuous poses. Labels are opaque throughout.
export function overlapExample(a, b) {
  const aa = new Map(a.map((s) => [s.id, s])),
    bb = new Map(b.map((s) => [s.id, s]));
  const shared = a.filter((s) => bb.has(s.id)).length;
  if (!shared) return null;
  const points = [...a, ...b.filter((s) => !aa.has(s.id))].map((s) => ({
    position: s.position,
    species: JSON.stringify([
      s.species,
      aa.has(s.id),
      bb.has(s.id),
      s.id === a[0].id,
      s.id === b[0].id,
    ]),
  }));
  const distances = [];
  for (let i = 0; i < points.length; i++)
    for (let j = 0; j < i; j++)
      distances.push(distance(points[i].position, points[j].position));
  distances.sort((x, y) => x - y);
  return { shared, points, distances };
}
const key = (a, b, e) => `${a}:${b}:${e.shared}:${e.points.length}`;
function same(a, b, epsilon) {
  // Necessary invariant only; proper rigid registration makes the decision.
  if (
    a.distances.length !== b.distances.length ||
    a.distances.some(
      (d, i) => Math.abs(d - b.distances[i]) > 2 * epsilon + 1e-9,
    )
  )
    return false;
  return !!register(a.points, b.points, epsilon);
}
export function acceptsOverlap(rules, aType, bType, a, b) {
  const example = overlapExample(a, b);
  if (!example) return true; // No overlap: this rule makes no claim about proximity.
  return (rules.catalogue[key(aType, bType, example)] || []).some((r) =>
    same(r, example, rules.epsilon),
  );
}
export function* learnOverlapRules(grammar) {
  const occurrences = grammar.types.flatMap((t) =>
    t.occurrences.map((o) => ({
      type: t.id,
      anchor: o.anchor,
      sites: o.mapping.map((i) => ({
        id: o.ids[i],
        ...grammar.atoms[o.ids[i]],
      })),
    })),
  );
  const catalogue = Object.create(null);
  let pairs = 0,
    classes = 0;
  for (let i = 0; i < occurrences.length; i++) {
    const a = occurrences[i];
    for (let j = 0; j < occurrences.length; j++) {
      const b = occurrences[j];
      if (i === j || a.anchor === b.anchor) continue;
      const example = overlapExample(a.sites, b.sites);
      if (!example) continue;
      pairs++;
      const k = key(a.type, b.type, example),
        bucket = (catalogue[k] ||= []);
      if (!bucket.some((r) => same(r, example, grammar.epsilon))) {
        bucket.push({ ...example, witness: [i, j] });
        classes++;
      }
    }
    if (i % 4 === 0)
      yield {
        kind: "overlap-learning",
        done: i + 1,
        total: occurrences.length,
        pairs,
        classes,
      };
  }
  return {
    schema: "observed-overlap-relation/1",
    policy: "observed-only",
    epsilon: grammar.epsilon,
    catalogue,
    pairs,
    classes,
    occurrences: occurrences.length,
    scope:
      "problem-defining observed-only geometric overlap restriction; unseen overlaps forbidden, disjoint supports unconstrained",
  };
}

export function overlapConstraint(grammar, rules, registry) {
  const sites = (c) =>
    c.meta.sites.map((id, i) => ({
      id,
      species: grammar.types[c.meta.type].sites[i].species,
      position: registry.points[Number(id.slice(1))].position,
    }));
  const cache = new Map();
  const counters = { checks: 0, rejections: 0 };
  const constraint = (c, engine) => {
    if (!c.meta) return null;
    const neighbors = new Set();
    // Exact dependency domain: all assigned section sites, including mark-only
    // points. Kernel refresh/rollback already traverses these point incidences.
    for (const id of c.meta.sites)
      for (const rows of engine.points.get(id)?.marks.values() || [])
        for (const row of rows)
          if (engine.placed.has(row.owner) && row.owner !== c.id)
            neighbors.add(row.owner);
    for (const id of neighbors) {
      const other = engine.candidates.get(id);
      if (!other?.meta) continue;
      const pair = JSON.stringify([c.id, id]);
      let allowed = cache.get(pair);
      if (allowed === undefined) {
        counters.checks++;
        allowed = acceptsOverlap(
          rules,
          c.meta.type,
          other.meta.type,
          sites(c),
          sites(other),
        );
        // Cache bounds affect performance only, never whether a rule is applied.
        if (cache.size >= 20000) cache.clear();
        cache.set(pair, allowed);
      }
      if (!allowed) {
        counters.rejections++;
        return "unobserved-overlap";
      }
    }
    return null;
  };
  constraint.counters = counters;
  return constraint;
}

export function verifyOverlaps(grammar, rules, registry, candidates, selected) {
  const sites = (c) =>
    c.meta.sites.map((id, i) => ({
      id,
      species: grammar.types[c.meta.type].sites[i].species,
      position: registry.points[Number(id.slice(1))].position,
    }));
  let checked = 0;
  for (let i = 0; i < selected.length; i++)
    for (let j = 0; j < i; j++) {
      const a = candidates.get(selected[i]),
        b = candidates.get(selected[j]);
      if (!a.meta.sites.some((id) => b.meta.sites.includes(id))) continue;
      checked++;
      if (!acceptsOverlap(rules, a.meta.type, b.meta.type, sites(a), sites(b)))
        return { legal: false, checked, conflict: [a.id, b.id] };
    }
  return { legal: true, checked };
}
