const sortedUnique = (values) => [...new Set(values)].sort((first, second) => first - second);

function supportKey(support) {
  return sortedUnique(support).join(":");
}

function speciesFormula(species, support) {
  const counts = new Map();
  support.forEach((index) => counts.set(species[index], (counts.get(species[index]) || 0) + 1));
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([element, count]) => `${element}${count === 1 ? "" : count}`).join("");
}

function supportSiteFingerprint(species, support, site, distance, tolerance) {
  return `${species[site]}|${support.filter((other) => other !== site).map((other) =>
    `${species[other]}:${Math.round(distance(site, other) / tolerance)}`).sort().join(",")}`;
}

function chiralityToken(species, support, distance, orientedVolume, tolerance) {
  if (typeof orientedVolume !== "function" || support.length < 4) return "unchecked";
  const fingerprints = new Map(support.map((site) => [site,
    supportSiteFingerprint(species, support, site, distance, tolerance)]));
  let bestKey = null;
  const signs = new Set();
  for (let a = 0; a < support.length - 3; a++) for (let b = a + 1; b < support.length - 2; b++) {
    for (let c = b + 1; c < support.length - 1; c++) for (let d = c + 1; d < support.length; d++) {
      const ordered = [support[a], support[b], support[c], support[d]]
        .sort((first, second) => fingerprints.get(first).localeCompare(fingerprints.get(second)));
      if (new Set(ordered.map((site) => fingerprints.get(site))).size < 4) continue;
      const volume = orientedVolume(...ordered);
      if (!Number.isFinite(volume) || Math.abs(volume) <= tolerance ** 3) continue;
      const key = `${ordered.map((site) => fingerprints.get(site)).join(";")}|${Math.round(Math.abs(volume) / tolerance ** 3)}`;
      if (bestKey === null || key < bestKey) {
        bestKey = key;
        signs.clear();
        signs.add(Math.sign(volume));
      } else if (key === bestKey) signs.add(Math.sign(volume));
    }
  }
  if (bestKey === null || signs.size !== 1) return "unresolved";
  return signs.has(1) ? "+" : "-";
}

function coloredMetricSignature(species, support, distance, tolerance, orientedVolume) {
  const colors = support.map((index) => species[index]).sort();
  const pairs = [];
  support.forEach((first, firstIndex) => support.slice(firstIndex + 1).forEach((second) => {
    const pair = [species[first], species[second]].sort().join("-");
    pairs.push(`${pair}:${Math.round(distance(first, second) / tolerance)}`);
  }));
  return `${colors.join(",")}|${pairs.sort().join(",")}|chi:${chiralityToken(species, support, distance, orientedVolume, tolerance)}`;
}

function adaptiveLensSupport(first, second, atomCount, distance, spacing) {
  const ranked = Array.from({ length: atomCount }, (_, index) => ({
    index,
    score: (distance(first, index) + distance(second, index)) / spacing,
  })).sort((a, b) => a.score - b.score || a.index - b.index);
  const minimum = Math.min(4, atomCount);
  const maximum = Math.min(8, atomCount);
  let size = minimum;
  let largestGap = 0;
  for (let index = minimum - 1; index < maximum - 1; index++) {
    const gap = ranked[index + 1].score - ranked[index].score;
    if (gap > largestGap) { largestGap = gap; size = index + 1; }
  }
  if (largestGap < .12) size = Math.min(6, maximum);
  return sortedUnique(ranked.slice(0, size).map((entry) => entry.index));
}

function groupRecurringCandidates(candidates, species, distance, tolerance, minimumOccurrences, orientedVolume) {
  const deduped = new Map();
  candidates.forEach((candidate) => {
    const key = supportKey(candidate.support);
    const existing = deduped.get(key);
    if (!existing || (existing.kind !== "coordination" && candidate.kind === "coordination")) deduped.set(key, candidate);
  });
  const groups = new Map();
  deduped.forEach((candidate) => {
    const signature = coloredMetricSignature(species, candidate.support, distance, tolerance, orientedVolume);
    const group = groups.get(signature) || { signature, occurrences: [], kinds: new Set() };
    group.occurrences.push(candidate);
    group.kinds.add(candidate.kind);
    groups.set(signature, group);
  });
  return [...groups.values()].filter((group) => group.occurrences.length >= minimumOccurrences)
    .sort((first, second) => second.occurrences.length - first.occurrences.length
      || second.occurrences[0].support.length - first.occurrences[0].support.length
      || first.signature.localeCompare(second.signature));
}

function chooseCoverOccurrences(groups, uncovered, selected, selectedKeys) {
  const choices = groups.flatMap((group) => group.occurrences.map((occurrence) => ({ group, occurrence })));
  while (uncovered.size) {
    const scored = choices.map((choice) => ({
      ...choice,
      gain: choice.occurrence.support.reduce((sum, index) => sum + Number(uncovered.has(index)), 0),
    })).filter((choice) => choice.gain > 0)
      .sort((first, second) => second.gain - first.gain
        || Number(first.occurrence.kind !== "coordination") - Number(second.occurrence.kind !== "coordination")
        || second.group.occurrences.length - first.group.occurrences.length
        || first.group.signature.localeCompare(second.group.signature)
        || first.occurrence.anchor - second.occurrence.anchor);
    if (!scored.length) break;
    const winner = scored[0];
    const key = supportKey(winner.occurrence.support);
    if (!selectedKeys.has(key)) {
      selected.push(winner);
      selectedKeys.add(key);
    }
    winner.occurrence.support.forEach((index) => uncovered.delete(index));
  }
}

function addRecurrenceWitnesses(selected, selectedKeys) {
  const groups = new Map();
  selected.forEach((choice) => {
    const rows = groups.get(choice.group.signature) || [];
    rows.push(choice);
    groups.set(choice.group.signature, rows);
  });
  groups.forEach((rows) => {
    if (rows.length >= 2) return;
    const alternative = rows[0].group.occurrences.find((occurrence) => !selectedKeys.has(supportKey(occurrence.support)));
    if (!alternative) return;
    selected.push({ group: rows[0].group, occurrence: alternative });
    selectedKeys.add(supportKey(alternative.support));
  });
}

function selectedOccurrenceComponents(selected) {
  const adjacency = Array.from({ length: selected.length }, () => []);
  for (let first = 0; first < selected.length; first++) for (let second = first + 1; second < selected.length; second++) {
    if (sharedSites(selected[first].occurrence.support, selected[second].occurrence.support).length < 2) continue;
    adjacency[first].push(second);
    adjacency[second].push(first);
  }
  const labels = new Array(selected.length).fill(-1);
  let component = 0;
  labels.forEach((_, seed) => {
    if (labels[seed] >= 0) return;
    const queue = [seed];
    labels[seed] = component;
    while (queue.length) adjacency[queue.shift()].forEach((neighbor) => {
      if (labels[neighbor] >= 0) return;
      labels[neighbor] = component;
      queue.push(neighbor);
    });
    component++;
  });
  return { labels, count: component };
}

function addRecurringSteinerOccurrences(selected, selectedKeys) {
  while (selected.length > 1) {
    const components = selectedOccurrenceComponents(selected);
    if (components.count <= 1) return;
    const admittedGroups = new Map(selected.map((choice) => [choice.group.signature, choice.group]));
    const pool = [];
    admittedGroups.forEach((group) => group.occurrences.forEach((occurrence) => {
      const key = supportKey(occurrence.support);
      if (!pool.some((entry) => entry.key === key)) pool.push({ key, group, occurrence });
    }));
    pool.sort((first, second) => first.group.signature.localeCompare(second.group.signature)
      || first.key.localeCompare(second.key));
    const poolIndex = new Map(pool.map((entry, index) => [entry.key, index]));
    const adjacency = Array.from({ length: pool.length }, () => []);
    for (let first = 0; first < pool.length; first++) for (let second = first + 1; second < pool.length; second++) {
      if (sharedSites(pool[first].occurrence.support, pool[second].occurrence.support).length < 2) continue;
      adjacency[first].push(second);
      adjacency[second].push(first);
    }
    const selectedComponentByPool = new Map();
    selected.forEach((choice, index) => selectedComponentByPool.set(poolIndex.get(supportKey(choice.occurrence.support)), components.labels[index]));
    const queue = [];
    const previous = new Array(pool.length).fill(-1);
    const origin = new Array(pool.length).fill(-1);
    selectedComponentByPool.forEach((component, index) => {
      if (component !== 0) return;
      queue.push(index);
      origin[index] = component;
    });
    let target = -1;
    while (queue.length && target < 0) {
      const current = queue.shift();
      for (const neighbor of adjacency[current]) {
        if (origin[neighbor] >= 0) continue;
        origin[neighbor] = origin[current];
        previous[neighbor] = current;
        if (selectedComponentByPool.has(neighbor) && selectedComponentByPool.get(neighbor) !== 0) {
          target = neighbor;
          break;
        }
        queue.push(neighbor);
      }
    }
    if (target < 0) return;
    const path = [];
    for (let current = target; current >= 0; current = previous[current]) path.push(current);
    let added = 0;
    path.reverse().forEach((index) => {
      const entry = pool[index];
      if (selectedKeys.has(entry.key)) return;
      selected.push({ group: entry.group, occurrence: entry.occurrence });
      selectedKeys.add(entry.key);
      added++;
    });
    if (!added) return;
  }
}

function residualComponents(uncovered, atomCount, distance, spacing, maximumSites = 8) {
  const remaining = new Set(uncovered);
  const components = [];
  while (remaining.size) {
    const seed = Math.min(...remaining);
    const queue = [seed];
    const component = [];
    remaining.delete(seed);
    while (queue.length && component.length < maximumSites) {
      const current = queue.shift();
      component.push(current);
      const capacity = maximumSites - component.length - queue.length;
      [...remaining].sort((first, second) => distance(current, first) - distance(current, second) || first - second)
        .filter((candidate) => distance(current, candidate) <= spacing * 1.35)
        .slice(0, Math.max(0, capacity)).forEach((candidate) => {
          remaining.delete(candidate);
          queue.push(candidate);
        });
    }
    components.push(sortedUnique(component));
  }
  return components;
}

function sharedSites(first, second) {
  const secondSet = new Set(second);
  return first.filter((index) => secondSet.has(index));
}

function boundedReplayConnectors(supports, distance, spacing, maximumReach = 2.5) {
  if (!supports.length) return { connectors: [], reachable: new Set(), disconnected: 0, seed: 0 };
  const seed = supports.reduce((best, support, index) => support.length > best.size
    ? { index, size: support.length } : best, { index: 0, size: -1 }).index;
  const reachable = new Set([seed]);
  const remaining = new Set(supports.map((_, index) => index).filter((index) => index !== seed));
  const reachableSupports = [{ support: supports[seed], source: seed }];
  const connectors = [];
  while (remaining.size) {
    let advanced = false;
    [...remaining].sort((first, second) => first - second).forEach((index) => {
      if ([...reachableSupports].some((entry) => sharedSites(entry.support, supports[index]).length >= 2)) {
        remaining.delete(index);
        reachable.add(index);
        reachableSupports.push({ support: supports[index], source: index });
        advanced = true;
      }
    });
    if (advanced) continue;
    let best = null;
    remaining.forEach((target) => reachableSupports.forEach((parent) => {
      if (parent.support.length < 2) return;
      parent.support.forEach((first) => supports[target].forEach((second) => {
        const separation = distance(first, second);
        if (!best || separation < best.separation
          || (separation === best.separation && target < best.target)) {
          best = { target, parent, separation };
        }
      }));
    }));
    if (!best || best.separation > spacing * maximumReach) break;
    const parentAtoms = best.parent.support.slice().sort((first, second) => {
      const firstDistance = Math.min(...supports[best.target].map((target) => distance(first, target)));
      const secondDistance = Math.min(...supports[best.target].map((target) => distance(second, target)));
      return firstDistance - secondDistance || first - second;
    }).slice(0, 2);
    const support = sortedUnique([...supports[best.target], ...parentAtoms]);
    connectors.push(support);
    remaining.delete(best.target);
    reachable.add(best.target);
    reachableSupports.push({ support, source: null });
  }
  return { connectors, reachable, disconnected: remaining.size, seed };
}

/**
 * Discover an exact complete cover without assuming that every support is
 * centred on an atom. Atom coordination shells are the elementary candidates;
 * bond-lens candidates are finite irregular colored metric sets. A signed
 * role-ordered volume distinguishes supported enantiomorphs. Recurring
 * coordination supports are preferred, while centre-free lenses are admitted
 * when those elementary supports cannot cover the observation. Remaining
 * atoms become explicit connected residual terminals.
 */
export function discoverIrregularCover({
  species,
  distance: rawDistance,
  referenceSpacing,
  shellRadius = 1.38,
  minimumOccurrences = 2,
  metricTolerance = .025,
  orientedVolume = null,
}) {
  if (!Array.isArray(species) || !species.length) throw new Error("irregular cover requires species");
  if (!(referenceSpacing > 0)) throw new Error("irregular cover requires a positive reference spacing");
  const atomCount = species.length;
  const cache = Array.from({ length: atomCount }, () => new Array(atomCount));
  const distance = (first, second) => {
    if (first === second) return 0;
    const lower = Math.min(first, second), upper = Math.max(first, second);
    if (cache[lower][upper] === undefined) cache[lower][upper] = rawDistance(lower, upper);
    return cache[lower][upper];
  };
  const coordinationCandidates = [];
  const nearest = [];
  for (let center = 0; center < atomCount; center++) {
    const ranked = Array.from({ length: atomCount }, (_, index) => index).filter((index) => index !== center)
      .sort((first, second) => distance(center, first) - distance(center, second) || first - second);
    nearest.push(ranked.slice(0, Math.min(4, ranked.length)));
    const support = [center, ...ranked.filter((index) => distance(center, index) <= referenceSpacing * shellRadius)];
    coordinationCandidates.push({ anchor: center, support: sortedUnique(support), kind: "coordination" });
  }
  const lensCandidates = [];
  const seenPairs = new Set();
  nearest.forEach((neighbors, first) => neighbors.forEach((second) => {
    const pair = first < second ? `${first}:${second}` : `${second}:${first}`;
    if (seenPairs.has(pair) || distance(first, second) > referenceSpacing * 1.45) return;
    seenPairs.add(pair);
    lensCandidates.push({
      anchor: Math.min(first, second),
      support: adaptiveLensSupport(first, second, atomCount, distance, referenceSpacing),
      kind: "bond-lens",
      bond: [Math.min(first, second), Math.max(first, second)],
    });
  }));
  const tolerance = referenceSpacing * metricTolerance;
  const coordinationGroups = groupRecurringCandidates(coordinationCandidates, species, distance, tolerance, minimumOccurrences, orientedVolume);
  const lensGroups = groupRecurringCandidates(lensCandidates, species, distance, tolerance, minimumOccurrences, orientedVolume);
  const uncovered = new Set(Array.from({ length: atomCount }, (_, index) => index));
  const selected = [];
  const selectedKeys = new Set();
  chooseCoverOccurrences(coordinationGroups, uncovered, selected, selectedKeys);
  if (uncovered.size) chooseCoverOccurrences(lensGroups, uncovered, selected, selectedKeys);
  addRecurrenceWitnesses(selected, selectedKeys);
  addRecurringSteinerOccurrences(selected, selectedKeys);
  const selectedAtoms = new Set(selected.flatMap((choice) => choice.occurrence.support));
  uncovered.clear();
  for (let index = 0; index < atomCount; index++) if (!selectedAtoms.has(index)) uncovered.add(index);

  const selectedGroups = [...new Map(selected.map((choice) => [choice.group.signature, choice.group])).values()];
  const types = selectedGroups.map((group, type) => {
    const representativeChoice = selected.find((choice) => choice.group.signature === group.signature);
    const representative = representativeChoice.occurrence;
    return {
      type,
      signature: group.signature,
      support: representative.support.slice(),
      anchor: representative.anchor,
      occurrenceCount: selected.filter((choice) => choice.group.signature === group.signature).length,
      observedCandidateCount: group.occurrences.length,
      kinds: [...group.kinds].sort(),
      residual: false,
      chirality: group.signature.split("|chi:").at(-1),
      formula: speciesFormula(species, representative.support),
      geometry: representative.kind === "bond-lens" ? "center-free bond-lens polyhedron" : "recurring coordination polyhedron",
    };
  });
  const typeBySignature = new Map(types.map((type) => [type.signature, type.type]));
  const placements = selected.map((choice) => ({
    center: choice.occurrence.anchor,
    support: choice.occurrence.support.slice(),
    type: typeBySignature.get(choice.group.signature),
    residual: false,
    seedKind: choice.occurrence.kind,
  }));

  const uncoveredResidualSupports = residualComponents(uncovered, atomCount, distance, referenceSpacing);
  const replayAudit = boundedReplayConnectors([
    ...selected.map((choice) => choice.occurrence.support),
    ...uncoveredResidualSupports,
  ], distance, referenceSpacing);
  const residualRecords = [
    ...uncoveredResidualSupports.map((support) => ({ support, kind: "residual" })),
    ...replayAudit.connectors.map((support) => ({ support, kind: "connector" })),
  ];
  const residualGroups = new Map();
  residualRecords.forEach((record) => {
    const { support } = record;
    const signature = coloredMetricSignature(species, support, distance, tolerance, orientedVolume);
    const group = residualGroups.get(signature) || [];
    group.push(record);
    residualGroups.set(signature, group);
  });
  const residualTypes = [...residualGroups.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([signature, records], offset) => ({
      type: types.length + offset,
      signature,
      support: records[0].support.slice(),
      anchor: records[0].support[0],
      occurrenceCount: records.length,
      observedCandidateCount: records.length,
      kinds: [...new Set(records.map((record) => record.kind))].sort(),
      residual: true,
      chirality: signature.split("|chi:").at(-1),
      formula: speciesFormula(species, records[0].support),
      geometry: records.some((record) => record.kind === "connector")
        ? "explicit bounded replay connector"
        : records[0].support.length > 1 ? "explicit connected gap cluster" : "explicit residual atom",
    }));
  const residualTypeBySignature = new Map(residualTypes.map((type) => [type.signature, type.type]));
  residualRecords.forEach(({ support, kind }) => {
    const signature = coloredMetricSignature(species, support, distance, tolerance, orientedVolume);
    placements.push({ center: support[0], support: support.slice(), type: residualTypeBySignature.get(signature), residual: true, seedKind: kind });
  });
  const covered = new Set(placements.flatMap((placement) => placement.support));
  return {
    types: [...types, ...residualTypes],
    residualTypes,
    placements,
    coveredAtoms: covered.size,
    complete: covered.size === atomCount,
    recurringCoordinationClasses: coordinationGroups.length,
    recurringCenterFreeClasses: lensGroups.length,
    selectedCenterFreeOccurrences: placements.filter((placement) => placement.seedKind === "bond-lens").length,
    residualAtoms: uncoveredResidualSupports.reduce((sum, support) => sum + support.length, 0),
    replayConnectorCount: replayAudit.connectors.length,
    disconnectedReplayComponents: replayAudit.disconnected,
    replaySeedPlacementIndex: replayAudit.seed,
    minimumOccurrences,
    metricToleranceFraction: metricTolerance,
  };
}

export { coloredMetricSignature };
