import {
  add,
  sub,
  mul,
  distance,
  norm,
  relative,
  compose,
  transpose,
  product,
  keySites,
  canonicalSupport,
  validateAtoms,
  freeze,
} from "./continuous-geometry.mjs";

export function* identifyClusters(
  input,
  { tolerance = 1e-3, maximumSupport = 13, hierarchy = false } = {},
) {
  if (
    !Number.isFinite(tolerance) ||
    tolerance <= 0 ||
    !Number.isInteger(maximumSupport) ||
    maximumSupport < 3 ||
    maximumSupport > 64
  )
    throw Error(
      "Use a positive tolerance and a support budget between 3 and 64 atoms.",
    );
  const atoms = validateAtoms(input),
    n = atoms.length;
  if (n > 1600)
    throw Error(
      "This browser learner supports 1,600 observed atoms per fit; use the research console for larger inputs.",
    );
  const neighbors = atoms.map((a, i) =>
    atoms
      .map((b, j) => ({ j, d: distance(a.position, b.position) }))
      .filter((x) => x.j !== i)
      .sort((a, b) => a.d - b.d || a.j - b.j),
  );
  const minimum = Math.min(...neighbors.map((a) => a[0].d));
  if (tolerance >= minimum / 4)
    throw Error(
      "Matching tolerance must be smaller than a quarter of the closest observed separation.",
    );
  const scale = [...neighbors.map((a) => a[0].d)].sort((a, b) => a - b)[
    Math.floor(n / 2)
  ];
  const supports = new Map(),
    types = new Map(),
    trace = [];
  let molecularClosure = false;
  const components = [],
    owner = new Map();
  const propose = (ids, kind) => {
    if (molecularClosure) {
      if (ids.some((i) => !owner.has(i))) return;
      ids = ids.flatMap((i) => owner.get(i));
    }
    ids = [...new Set(ids)].sort((a, b) => a - b);
    if (
      ids.length >= 3 &&
      ids.length <= maximumSupport &&
      !supports.has(ids.join(","))
    )
      supports.set(ids.join(","), { ids, kind });
  };
  // Compact connected components recover molecular supports from positions.
  const visited = new Set();
  for (let i = 0; i < n; i++)
    if (!visited.has(i)) {
      const queue = [i];
      visited.add(i);
      for (let k = 0; k < queue.length; k++)
        for (const nb of neighbors[queue[k]]) {
          if (nb.d > scale * 1.32) break;
          if (!visited.has(nb.j)) {
            visited.add(nb.j);
            queue.push(nb.j);
          }
        }
      components.push(queue);
    }
  const componentTypes = new Map();
  for (const ids of components) {
    if (ids.length < 3 || ids.length > maximumSupport) continue;
    const c = canonicalSupport(
      ids.map((i) => atoms[i]),
      tolerance,
    );
    if (!c) continue;
    if (!componentTypes.has(c.key)) componentTypes.set(c.key, []);
    componentTypes.get(c.key).push(ids);
  }
  const recurringComponents = [...componentTypes.values()]
    .filter((rows) => rows.length >= 2)
    .flat();
  // Use molecular closure only when repeated isolated components dominate
  // the observation. Unrecognized/cropped components remain seed residuals.
  molecularClosure =
    recurringComponents.reduce((s, ids) => s + ids.length, 0) > n / 2;
  if (molecularClosure) {
    recurringComponents.forEach((ids) => ids.forEach((i) => owner.set(i, ids)));
    for (const ids of recurringComponents) {
      propose(ids, "connected component");
      const contacts = recurringComponents
        .filter((other) => other !== ids)
        .map((other) => ({
          other,
          d: Math.min(
            ...ids.flatMap((i) =>
              other.map((j) => distance(atoms[i].position, atoms[j].position)),
            ),
          ),
        }));
      const nearest = Math.min(...contacts.map((x) => x.d));
      for (const { other, d } of contacts)
        if (d <= nearest * 1.18 + tolerance)
          propose([...ids, ...other], "molecular contact neighborhood");
    }
  } else {
    for (const ids of components) propose(ids, "connected component");
  }
  for (let i = 0; i < n; i++) {
    const shell = neighbors[i]
      .filter((x) => x.d <= neighbors[i][0].d * 1.18)
      .map((x) => x.j);
    propose([i, ...shell], "adaptive shell");
    // Center-free bond neighborhoods supplement local shells and molecules.
    for (const nb of neighbors[i].filter(
      (x) =>
        x.d <= neighbors[i][Math.min(1, neighbors[i].length - 1)].d + tolerance,
    )) {
      const ids = [
        i,
        nb.j,
        ...shell,
        ...neighbors[nb.j]
          .filter((x) => x.d <= neighbors[nb.j][0].d * 1.18)
          .map((x) => x.j),
      ];
      propose(ids, "bond neighborhood");
    }
    if (i % 16 === 0)
      yield {
        phase: "proposing",
        done: i,
        total: n,
        edges: neighbors[i].slice(0, 6).map((x) => [i, x.j]),
        message:
          "Testing connected supports and overlapping bond neighborhoods",
      };
  }
  let done = 0;
  for (const support of supports.values()) {
    const canonical = canonicalSupport(
      support.ids.map((i) => atoms[i]),
      tolerance,
    );
    if (canonical) {
      let type = types.get(canonical.key);
      if (!type) {
        type = {
          id: types.size,
          key: canonical.key,
          sites: canonical.sites,
          kind: support.kind,
          occurrences: [],
          symmetries: canonical.frames.map((r) =>
            product(transpose(canonical.pose.r), r),
          ),
          level: 0,
        };
        types.set(canonical.key, type);
      }
      type.occurrences.push({ ids: support.ids, pose: canonical.pose });
    }
    if (++done % 12 === 0)
      yield {
        phase: "matching",
        done,
        total: supports.size,
        edges: support.ids.slice(1).map((i) => [support.ids[0], i]),
        message: "Comparing full colored supports under proper rotations",
      };
  }
  let retained = [...types.values()].filter((t) => t.occurrences.length >= 2);
  const covered = new Set(
    retained.flatMap((t) => t.occurrences.flatMap((o) => o.ids)),
  );
  const residuals = atoms.map((_, i) => i).filter((i) => !covered.has(i));
  retained.forEach((t, i) => {
    t.id = i;
  });
  const occurrences = retained.flatMap((t) =>
    t.occurrences.map((o) => ({ ...o, type: t.id, id: 0 })),
  );
  occurrences.forEach((o, i) => (o.id = i));
  const grammar = {
    schema: "continuous-gcts/1",
    atoms,
    types: retained,
    occurrences,
    residuals,
    scale,
    minimum,
    tolerance,
    ports: [],
    macroEnabled: hierarchy,
    trace,
    audit: {
      observedAtoms: n,
      coveredAtoms: covered.size,
      residualAtoms: residuals.length,
      completeAtomicCover: covered.size + residuals.length === n,
      finiteObservation: true,
      targetUsed: false,
      arbitraryRotation: true,
      periodicImagesUsed: false,
    },
  };
  // Optional clusters of clusters: exact repeated unions of two overlapping
  // primitive occurrences; admission requires two atom-disjoint witnesses.
  if (hierarchy) {
    const macros = new Map();
    const testedUnions = new Set();
    let checks = 0;
    for (let a = 0; a < occurrences.length; a++)
      for (let b = a + 1; b < occurrences.length; b++) {
        if (++checks % 5000 === 0)
          yield {
            phase: "promotion",
            done: a,
            total: occurrences.length,
            message: "Testing repeated unions of overlapping clusters",
          };
        const one = occurrences[a],
          two = occurrences[b];
        if (!one.ids.some((i) => two.ids.includes(i))) continue;
        const ids = [...new Set([...one.ids, ...two.ids])].sort(
          (x, y) => x - y,
        );
        if (
          ids.length > maximumSupport ||
          ids.length <= Math.max(one.ids.length, two.ids.length)
        )
          continue;
        const unionKey = ids.join(",");
        if (testedUnions.has(unionKey)) continue;
        testedUnions.add(unionKey);
        const c = canonicalSupport(
          ids.map((i) => atoms[i]),
          tolerance,
        );
        if (!c) continue;
        if (!macros.has(c.key))
          macros.set(c.key, {
            key: c.key,
            sites: c.sites,
            kind: "cluster of clusters",
            level: 1,
            symmetries: c.frames.map((r) => product(transpose(c.pose.r), r)),
            occurrences: [],
          });
        const t = macros.get(c.key);
        if (!t.occurrences.some((o) => o.ids.join(",") === ids.join(",")))
          t.occurrences.push({ ids, pose: c.pose });
      }
    // Promotion is a bounded first hierarchy level, not exhaustive mining.
    // Favor independently witnessed frequent types; bound the quadratic port
    // expansion produced by admitting every possible union.
    let promoted = 0;
    for (const t of [...macros.values()].sort(
      (a, b) =>
        b.occurrences.length - a.occurrences.length ||
        a.key.localeCompare(b.key),
    )) {
      if (promoted >= 12) break;
      if (
        !types.has(t.key) &&
        t.occurrences.some((o, i) =>
          t.occurrences
            .slice(i + 1)
            .some((p) => !o.ids.some((k) => p.ids.includes(k))),
        )
      ) {
        t.id = retained.length;
        retained.push(t);
        for (const o of t.occurrences)
          occurrences.push({ ...o, type: t.id, id: occurrences.length });
        promoted++;
      }
    }
    grammar.audit.promotionTypeLimit = 12;
    grammar.audit.promotedTypes = promoted;
    grammar.audit.testedUnionSupports = testedUnions.size;
  }
  const byAtom = new Map();
  for (const o of occurrences)
    for (const i of o.ids) {
      if (!byAtom.has(i)) byAtom.set(i, []);
      byAtom.get(i).push(o);
    }
  const pairs = new Set(),
    portMap = new Map();
  let count = 0;
  for (const parent of occurrences) {
    const children = new Set(parent.ids.flatMap((i) => byAtom.get(i) || []));
    for (const child of children) {
      if (
        parent.id === child.id ||
        child.ids.every((i) => parent.ids.includes(i))
      )
        continue;
      const pair = `${parent.id}:${child.id}`;
      if (pairs.has(pair)) continue;
      pairs.add(pair);
      const pose = relative(parent.pose, child.pose),
        ct = retained[child.type],
        pt = retained[parent.type];
      const orbit = pt.symmetries
        .map((r) => {
          const p = compose({ r, t: [0, 0, 0] }, pose);
          return {
            key: keySites(
              ct.sites.map((s) => ({
                species: s.species,
                position: compose(p, {
                  r: [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                  ],
                  t: s.position,
                }).t,
              })),
              tolerance,
            ),
            pose: p,
          };
        })
        .sort((a, b) => a.key.localeCompare(b.key))[0];
      const key = `${parent.type}>${child.type}|${orbit.key}`;
      if (!portMap.has(key))
        portMap.set(key, {
          id: portMap.size,
          key,
          parent: parent.type,
          child: child.type,
          pose: orbit.pose,
          overlap: parent.ids.filter((i) => child.ids.includes(i)).length,
          count: 0,
        });
      portMap.get(key).count++;
    }
    if (++count % 12 === 0)
      yield {
        phase: "connections",
        done: count,
        total: occurrences.length,
        message: "Learning witnessed relative poses and shared atomic sites",
      };
  }
  grammar.ports = [...portMap.values()];
  grammar.molecularCutoff = molecularClosure ? scale * 1.32 : null;
  grammar.audit.molecularSupportClosure = molecularClosure;
  grammar.audit.recurringMolecules = molecularClosure
    ? recurringComponents.length
    : 0;
  if (molecularClosure)
    for (const type of retained) {
      const seen = new Set();
      type.molecularGroups = [];
      for (let i = 0; i < type.sites.length; i++)
        if (!seen.has(i)) {
          const group = [i];
          seen.add(i);
          for (let k = 0; k < group.length; k++)
            for (let j = 0; j < type.sites.length; j++)
              if (
                !seen.has(j) &&
                distance(
                  type.sites[group[k]].position,
                  type.sites[j].position,
                ) <= grammar.molecularCutoff
              ) {
                seen.add(j);
                group.push(j);
              }
          type.molecularGroups.push(group);
        }
    }
  grammar.audit.observedConnections = pairs.size;
  grammar.audit.portClasses = grammar.ports.length;
  for (const type of retained)
    type.observedOrientationClasses = new Set(
      type.occurrences.map(
        (o) =>
          type.symmetries
            .map((s) =>
              product(o.pose.r, s)
                .flat()
                .map((v) => Math.round(v / 1e-5))
                .join(","),
            )
            .sort()[0],
      ),
    ).size;
  grammar.audit.hierarchyLevels = retained.some((t) => t.level === 1) ? 2 : 1;
  return freeze(grammar);
}

// Marking learns the empirical distribution of witnessed connections. This
// training loss measures reconstruction of counts, not held-out correctness.
export function* trainMarking(
  grammar,
  { channels = 4, reach = 2, epochs = 60 } = {},
) {
  if (
    !Number.isInteger(channels) ||
    channels < 1 ||
    channels > 64 ||
    !Number.isFinite(reach) ||
    reach <= 0 ||
    !Number.isInteger(epochs) ||
    epochs < 1 ||
    epochs > 1000
  )
    throw Error("Invalid marking dimensions, reach or training budget.");
  if (!grammar.ports.length)
    throw Error("No witnessed connections are available to train a marking.");
  const totals = new Map();
  grammar.ports.forEach((p) =>
    totals.set(p.parent, (totals.get(p.parent) || 0) + p.count),
  );
  const targets = grammar.ports.map((p) =>
    Math.log(
      (p.count + 1) /
        (totals.get(p.parent) +
          grammar.ports.filter((q) => q.parent === p.parent).length),
    ),
  );
  const features = grammar.ports.map((p) =>
    Array.from(
      { length: channels },
      (_, c) =>
        Math.cos(((c + 1) * norm(p.pose.t)) / (grammar.scale * reach)) *
        (1 + p.overlap / grammar.types[p.child].sites.length),
    ),
  );
  const weights = Array.from(
      { length: channels },
      (_, c) => Math.sin(c * 3.7 + 1) * 0.15,
    ),
    curve = [];
  for (let epoch = 0; epoch < epochs; epoch++) {
    let loss = 0;
    const gradient = weights.map(() => 0);
    features.forEach((x, i) => {
      const y = x.reduce((s, v, j) => s + v * weights[j], 0),
        e = y - targets[i];
      loss += e * e;
      x.forEach((v, j) => (gradient[j] += e * v));
    });
    for (let j = 0; j < channels; j++)
      weights[j] -=
        (0.03 * gradient[j]) / Math.max(1, features.length) / channels;
    curve.push(loss / Math.max(1, features.length));
    yield {
      epoch: epoch + 1,
      loss: curve.at(-1),
      weights: [...weights],
      samples: grammar.audit.observedConnections,
    };
  }
  const scores = Object.fromEntries(
    grammar.ports.map((p, i) => [
      p.id,
      features[i].reduce((s, v, j) => s + v * weights[j], 0),
    ]),
  );
  return freeze({
    id: `mark-${Date.now()}`,
    grammarKey: grammar.types.map((t) => t.key).join("/"),
    channels,
    reach,
    weights,
    curve,
    scores,
    samples: grammar.audit.observedConnections,
    objective: "Observed connection-frequency regression",
    heldoutValidated: false,
  });
}
