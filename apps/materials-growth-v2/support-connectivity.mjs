import { distance } from "./geometry.mjs";

export function components(count, supports) {
  const parent = Array.from({ length: count }, (_, i) => i);
  const root = (i) => (parent[i] === i ? i : (parent[i] = root(parent[i])));
  for (const ids of supports)
    for (const i of ids) parent[root(i)] = root(ids[0]);
  const groups = new Map();
  for (let i = 0; i < count; i++) {
    const key = root(i);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(i);
  }
  return [...groups.values()];
}

// Geometry-only proposals linking repeated disconnected finite supports. The
// distance criterion proposes contexts; it does not infer a chemical bond.
export function connectorProposals(atoms, proposals, types, epsilon) {
  const groups = components(
    atoms.length,
    proposals.map((p) => p.ids),
  );
  if (groups.length < 2 || !types.length) return [];
  const observed = new Set(
    types.flatMap((t) =>
      t.occurrences.map((o) => [...o.ids].sort((a, b) => a - b).join()),
    ),
  );
  const complete = groups.filter((g) => observed.has(g.join()));
  const anchors = new Set(
    types.flatMap((t) => t.occurrences.map((o) => o.anchor)),
  );
  const output = [];
  for (const group of complete) {
    // Prefer uncovered compilation anchors, retaining the small motif at its
    // existing anchors. If none are missing, inspect all potential interfaces.
    const missing = group.filter((i) => !anchors.has(i));
    for (const anchor of missing.length ? missing : group) {
      let nearest = Infinity;
      const neighbors = complete
        .filter((g) => g !== group)
        .map((g) => {
          const d = Math.min(
            ...group.flatMap((i) =>
              g.map((j) => distance(atoms[i].position, atoms[j].position)),
            ),
          );
          nearest = Math.min(nearest, d);
          return { g, d };
        });
      // Preserve the entire nearest component shell in one context: isolated
      // pair templates otherwise allow an internally closed dimer to satisfy
      // every local obligation without extending the surrounding material.
      const shell = neighbors.filter(
        ({ d }) => d <= nearest + Math.max(4 * epsilon, 0.08 * nearest),
      );
      const ids = [
        anchor,
        ...group.filter((i) => i !== anchor),
        ...shell.flatMap(({ g }) => g),
      ];
      if (shell.length && ids.length <= 38)
        output.push({ ids, role: "connector" });
    }
  }
  return output;
}

export function coverageReport(atoms, types) {
  const occurrences = types.flatMap((t) => t.occurrences);
  const covered = new Set(occurrences.flatMap((o) => o.ids));
  const anchors = new Set(occurrences.map((o) => o.anchor));
  const groups = components(
    atoms.length,
    occurrences.map((o) => o.ids),
  );
  return {
    atoms: atoms.length,
    coveredAtoms: covered.size,
    anchoredAtoms: anchors.size,
    missingAnchors: atoms.map((_, i) => i).filter((i) => !anchors.has(i)),
    supportComponents: groups.filter((g) => g.some((i) => covered.has(i)))
      .length,
    scope:
      "observed atomic supports, not volumetric coverage or a continuation certificate",
  };
}
