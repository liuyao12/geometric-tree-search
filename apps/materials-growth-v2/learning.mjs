import {
  distance,
  register,
  inverse,
  transform,
  compose,
  I,
} from "./geometry.mjs";
export function* discover(input, { epsilon = 0.025, neighbors = 8 } = {}) {
  if (input.length < 4 || input.length > 600)
    throw Error("Use 4–600 observed atoms for this browser experiment");
  if (!Number.isFinite(epsilon) || epsilon <= 0)
    throw Error("Positive positional error required");
  const atoms = input.map((a) => {
    if (
      typeof a.species !== "string" ||
      a.position?.length !== 3 ||
      !a.position.every(Number.isFinite)
    )
      throw Error("Invalid atom");
    if (a.occupancy != null && a.occupancy !== 1)
      throw Error("Resolve partial occupancy before learning");
    return { species: a.species, position: [...a.position] };
  });
  const rows = atoms.map((a, i) =>
    atoms
      .map((b, j) => ({ j, d: distance(a.position, b.position) }))
      .filter((x) => x.j !== i)
      .sort((a, b) => a.d - b.d),
  );
  if (Math.min(...rows.map((r) => r[0].d)) <= epsilon * 4)
    throw Error("Positional error exceeds a quarter of the closest spacing");
  const types = [],
    proposals = [];
  for (let i = 0; i < atoms.length; i++) {
    // Irregular nearest-neighbor collections; no formula, lattice or sphere
    // is supplied. The distinguished atom is only the t=1 compilation anchor.
    const cutoff = rows[i][Math.min(neighbors - 1, rows[i].length - 1)].d;
    const ids = [
      i,
      ...rows[i]
        .filter((x) => x.d <= cutoff + epsilon)
        .slice(0, 18)
        .map((x) => x.j),
    ];
    const sites = ids.map((j) => atoms[j]);
    proposals.push({ ids });
    let selected = null,
      registration = null;
    for (const type of types) {
      if (type.sites.length !== sites.length) continue;
      const r = register(type.sites, sites, epsilon);
      if (r) {
        selected = type;
        registration = r;
        break;
      }
    }
    if (!selected) {
      selected = {
        id: types.length,
        sites: sites.map((s) => ({
          species: s.species,
          position: s.position.map((v, k) => v - atoms[i].position[k]),
        })),
        occurrences: [],
      };
      types.push(selected);
      registration = {
        pose: { r: I, t: atoms[i].position },
        mapping: ids.map((_, i) => i),
        max: 0,
        rms: 0,
      };
    }
    selected.occurrences.push({
      anchor: i,
      ids,
      pose: registration.pose,
      mapping: registration.mapping,
      residual: registration.max,
    });
    if (i % 4 === 0)
      yield { kind: "discovery", done: i + 1, total: atoms.length, ids };
  }
  const recurring = types.filter((t) => t.occurrences.length >= 2);
  recurring.forEach((t, i) => (t.id = i));
  const occupied = new Set(
    recurring.flatMap((t) => t.occurrences.flatMap((o) => o.ids)),
  );
  // Pose transport between observed anchored supports. This finite evidence
  // set is not asserted exhaustive over SO(3).
  const byAnchor = new Map();
  recurring.forEach((t) =>
    t.occurrences.forEach((o) =>
      byAnchor.set(o.anchor, { type: t.id, pose: o.pose }),
    ),
  );
  const connections = [];
  for (const type of recurring)
    for (const o of type.occurrences)
      for (let k = 1; k < o.mapping.length; k++) {
        const target = byAnchor.get(o.ids[o.mapping[k]]);
        if (!target) continue;
        connections.push({
          parent: type.id,
          site: k,
          child: target.type,
          pose: compose(inverse(o.pose), target.pose),
        });
      }
  return {
    schema: "materials-v2-observation/1",
    atoms,
    types: recurring,
    epsilon,
    neighbors,
    connections,
    residuals: atoms.map((_, i) => i).filter((i) => !occupied.has(i)),
    proposals,
    poseUniverse:
      "observed relative poses, continuously registered; incomplete over SO(3)",
  };
}

export function* learnSections(grammar, { error = 0.05, epochs = 24 } = {}) {
  if (!grammar.types.length)
    throw Error(
      "No repeated supports were found. No growth claim is available.",
    );
  if (error < 0 || error >= 0.5)
    throw Error("Section error must be in [0, 0.5)");
  const labels = [...new Set(grammar.atoms.map((a) => a.species))].sort();
  const sections = grammar.types.map((t) => ({
    type: t.id,
    sites: t.sites.map((s) => ({
      position: [...s.position],
      values: labels.map(() => 0.5),
    })),
  }));
  const curve = [];
  for (let epoch = 0; epoch < epochs; epoch++) {
    let loss = 0,
      n = 0;
    for (const type of grammar.types)
      for (let i = 0; i < type.sites.length; i++)
        for (let c = 0; c < labels.length; c++) {
          const target =
            type.occurrences.reduce(
              (sum, o) =>
                sum +
                +(grammar.atoms[o.ids[o.mapping[i]]].species === labels[c]),
              0,
            ) / type.occurrences.length;
          const site = sections[type.id].sites[i],
            e = site.values[c] - target;
          loss += e * e;
          n++;
          site.values[c] -= 0.4 * e;
        }
    curve.push(loss / Math.max(1, n));
    yield {
      kind: "learning",
      epoch: epoch + 1,
      epochs,
      loss: curve.at(-1),
      sections: structuredClone(sections),
    };
  }
  // Common interval feasibility, not pairwise scalar similarity. Positional
  // uncertainty is handled separately by registration and point correspondence.
  for (const type of grammar.types)
    for (let i = 0; i < type.sites.length; i++) {
      const site = sections[type.id].sites[i];
      site.values = labels.map(
        (label) =>
          type.occurrences.reduce(
            (sum, o) =>
              sum + +(grammar.atoms[o.ids[o.mapping[i]]].species === label),
            0,
          ) / type.occurrences.length,
      );
      site.intervals = site.values.map((v) => [
        Math.max(0, v - error),
        Math.min(1, v + error),
      ]);
    }
  return {
    schema: "materials-v2-sections/1",
    version: JSON.stringify([
      grammar.epsilon,
      grammar.types.map((t) => t.sites),
      grammar.connections,
      error,
    ]),
    labels,
    sections,
    error,
    curve,
    scope: "learned hypothesis",
    representation:
      "scalar occupancy channels; positions rotate, label channels transform trivially",
    negativeEvidence:
      "unseen poses are unknown; supplied complete-crop absence is a problem-defining observation constraint",
    samples: grammar.types.reduce((s, t) => s + t.occurrences.length, 0),
  };
}
