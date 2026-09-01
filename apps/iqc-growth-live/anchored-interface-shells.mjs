const stableId = (value) => String(value);

function idSet(values, label) {
  if (!Array.isArray(values)) throw new TypeError(`${label} must be an array`);
  const ids = values.map(stableId);
  if (new Set(ids).size !== ids.length) throw new Error(`${label} contains duplicate site ids`);
  return new Set(ids);
}

/**
 * Audit a finite, contact-graph interface response domain.
 *
 * Shell 1 touches the newly attached batch, each subsequent movable shell
 * touches the preceding shell, and every atom in the outer movable shell must
 * touch a fixed anchor. Requiring every member of every shell to continue
 * outward prevents a disconnected or dangling branch from being presented as
 * an anchored substrate response.
 */
export function auditAnchoredInterfaceShells({
  freshIds,
  shellIds,
  anchorIds,
  contactPairs,
} = {}) {
  const fresh = idSet(freshIds, "freshIds");
  if (!Array.isArray(shellIds) || shellIds.length < 1) {
    throw new Error("anchored interface response requires at least one movable shell");
  }
  const shells = shellIds.map((ids, index) => idSet(ids, `shellIds[${index}]`));
  const anchors = idSet(anchorIds, "anchorIds");
  const populations = [fresh, ...shells, anchors];
  const occupied = new Set();
  populations.forEach((population) => population.forEach((id) => {
    if (occupied.has(id)) throw new Error("fresh, shell, and anchor site sets must be disjoint");
    occupied.add(id);
  }));
  if (!fresh.size || shells.some((shell) => !shell.size) || !anchors.size) {
    return Object.freeze({
      passed: false,
      reason: "fresh batch, every movable shell, and fixed anchors must be nonempty",
      shellCount: shells.length,
      freshSites: fresh.size,
      shellPopulations: Object.freeze(shells.map((shell) => shell.size)),
      anchorSites: anchors.size,
      danglingByLayer: Object.freeze([]),
      targetUsed: false,
    });
  }
  if (!Array.isArray(contactPairs)) throw new TypeError("contactPairs must be an array");
  const adjacency = new Map([...occupied].map((id) => [id, new Set()]));
  contactPairs.forEach((pair) => {
    if (!Array.isArray(pair) || pair.length !== 2) throw new Error("contact pair must contain two ids");
    const first = stableId(pair[0]);
    const second = stableId(pair[1]);
    if (first === second || !adjacency.has(first) || !adjacency.has(second)) return;
    adjacency.get(first).add(second);
    adjacency.get(second).add(first);
  });
  const layers = [fresh, ...shells, anchors];
  const danglingByLayer = [];
  for (let layer = 0; layer < layers.length - 1; layer++) {
    const outward = layers[layer + 1];
    const dangling = [...layers[layer]].filter((id) =>
      ![...(adjacency.get(id) || [])].some((neighbor) => outward.has(neighbor)));
    danglingByLayer.push(Object.freeze(dangling.sort()));
  }
  const passed = danglingByLayer.every((dangling) => dangling.length === 0);
  return Object.freeze({
    passed,
    reason: passed
      ? "every interface-response site has a contact path to the fixed outer anchors"
      : "one or more interface-response sites lacks an outward contact path to a fixed anchor",
    shellCount: shells.length,
    freshSites: fresh.size,
    shellPopulations: Object.freeze(shells.map((shell) => shell.size)),
    anchorSites: anchors.size,
    danglingByLayer: Object.freeze(danglingByLayer),
    allFreshConnectedToFirstShell: danglingByLayer[0]?.length === 0,
    allOuterShellConnectedToAnchors: danglingByLayer.at(-1)?.length === 0,
    targetUsed: false,
    claimBoundary: "This certificate establishes only a finite contact-graph path from the attached batch through explicitly movable substrate shells to fixed anchors. It is not an elastic Green function, stress equilibrium, force balance, continuum boundary condition, dynamics, or physical time.",
  });
}
