#!/usr/bin/env node

import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  enumeratePolycubeCoronaPlacements,
  polycubePlacementOrbitKeys,
  polycubeReciprocalPlacement,
  polycubeRootContactKey,
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const activeTypeIndices = String(args.get("active-types") ?? "3,25,29,43,44,53")
  .split(",")
  .map(Number)
  .filter(Number.isInteger);
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 5_000_000)));
const timeLimitMs = Math.max(1, numberArg("time-ms", 30_000));
const seed = Math.floor(numberArg("seed", 0));

const placementKey = placement => placement.cells
  .map(cell => cell.join(","))
  .sort()
  .join(";");
const overlaps = (left, right) => {
  const occupied = new Set(left.cells.map(cell => cell.join(",")));
  return right.cells.some(cell => occupied.has(cell.join(",")));
};
const popcount = value => {
  let count = 0;
  for (let remaining = value; remaining; remaining >>>= 1) count += remaining & 1;
  return count;
};

const catalog = enumeratePolycubeCoronaPlacements(candidate.voxels, 1);
const catalogByKey = new Map(catalog.map(placement => [placement.key, placement]));
const typeKeys = [...new Set(catalog.map(placement =>
  polycubeRootContactKey(candidate.voxels, placement)
))].sort();
const typeId = new Map(typeKeys.map((key, index) => [key, index]));
const active = new Set(activeTypeIndices);
const placementsByType = new Map(activeTypeIndices.map(index => [index, []]));
for (const placement of catalog) {
  const index = typeId.get(polycubeRootContactKey(candidate.voxels, placement));
  if (active.has(index)) placementsByType.get(index).push(placement);
}

const reciprocalOrbitRecords = new Map();
const outgoingTargetOrbitByPlacement = new Map();
for (const source of catalog) {
  const sourceType = typeId.get(polycubeRootContactKey(candidate.voxels, source));
  if (!active.has(sourceType)) continue;
  const reciprocalCells = polycubeReciprocalPlacement(candidate.voxels, source);
  if (!reciprocalCells) throw new Error(`Unable to reciprocate ${source.key}`);
  const reciprocalKey = placementKey(reciprocalCells);
  const reciprocal = catalogByKey.get(reciprocalKey);
  if (!reciprocal) throw new Error(`Reciprocal placement is absent from the corona catalog: ${reciprocalKey}`);
  const orbitKey = polycubePlacementOrbitKeys(candidate.voxels, reciprocal)[0];
  if (!reciprocalOrbitRecords.has(orbitKey)) reciprocalOrbitRecords.set(orbitKey, {
    orbit_key: orbitKey,
    representative: reciprocal,
    placement_keys: new Set(),
    incoming_types: new Set(),
    source_active_types: new Set()
  });
  const record = reciprocalOrbitRecords.get(orbitKey);
  record.placement_keys.add(reciprocal.key);
  record.incoming_types.add(typeId.get(polycubeRootContactKey(candidate.voxels, reciprocal)));
  record.source_active_types.add(sourceType);
  outgoingTargetOrbitByPlacement.set(source.key, orbitKey);
}

const orbitEntries = [...reciprocalOrbitRecords.values()]
  .sort((left, right) => left.orbit_key.localeCompare(right.orbit_key));
const orbitId = new Map(orbitEntries.map((entry, index) => [entry.orbit_key, index]));

const search = options => searchPolycubeCorona(candidate.voxels, {
  layers: 1,
  nodeLimit,
  timeLimitMs,
  seed,
  ...options
});

const rows = [];
const possibleEdges = new Map();
for (let incomingOrbit = 0; incomingOrbit < orbitEntries.length; incomingOrbit++) {
  const entry = orbitEntries[incomingOrbit];
  const incoming = entry.representative;
  const incomingType = typeId.get(polycubeRootContactKey(candidate.voxels, incoming));
  const baseline = search({ fixedPlacements: [incoming] });
  if (!baseline.success) {
    rows.push({
      incoming_orbit: incomingOrbit,
      incoming_type: incomingType,
      incoming_active: active.has(incomingType),
      extendable_corona: false,
      exhausted: baseline.exhausted,
      stopped_by: baseline.stopped_by,
      nodes: baseline.nodes
    });
    continue;
  }
  const baselineVerification = verifyPolycubeCoronaPatch(
    candidate.voxels,
    baseline.corona,
    1
  );
  if (!baselineVerification.verified) {
    throw new Error(`Baseline for incoming orbit ${incomingOrbit} failed verification: ${baselineVerification.reason}`);
  }

  const possibleOutgoingTypes = new Set();
  const possibleOutgoingOrbits = new Set();
  const possibleOutgoingPlacements = [];
  for (const outgoing of catalog) {
    const outgoingType = typeId.get(polycubeRootContactKey(candidate.voxels, outgoing));
    if (!active.has(outgoingType) || outgoing.key === incoming.key || overlaps(incoming, outgoing)) continue;
    const result = search({ fixedPlacements: [incoming, outgoing] });
    if (!result.success) {
      if (!result.exhausted) {
        throw new Error(`Outgoing transition test hit ${result.stopped_by} for incoming orbit ${incomingOrbit}`);
      }
      continue;
    }
    const verification = verifyPolycubeCoronaPatch(candidate.voxels, result.corona, 1);
    if (!verification.verified) {
      throw new Error(`Transition witness failed verification: ${verification.reason}`);
    }
    const targetOrbitKey = outgoingTargetOrbitByPlacement.get(outgoing.key);
    if (!targetOrbitKey) throw new Error(`Active outgoing placement has no reciprocal orbit: ${outgoing.key}`);
    const targetOrbit = orbitId.get(targetOrbitKey);
    possibleOutgoingTypes.add(outgoingType);
    possibleOutgoingOrbits.add(targetOrbit);
    possibleOutgoingPlacements.push({
      placement_key: outgoing.key,
      outgoing_type: outgoingType,
      target_incoming_orbit: targetOrbit,
      nodes: result.nodes
    });
    const edgeKey = `${incomingOrbit},${targetOrbit}`;
    if (!possibleEdges.has(edgeKey)) possibleEdges.set(edgeKey, {
      from: incomingOrbit,
      to: targetOrbit,
      outgoing_types: new Set(),
      placement_witnesses: 0
    });
    const edge = possibleEdges.get(edgeKey);
    edge.outgoing_types.add(outgoingType);
    edge.placement_witnesses += 1;
  }

  const subsetTrials = [];
  let minimumForcedSize = null;
  const minimumForcedTypeSets = [];
  const subsetMasks = Array.from(
    { length: (1 << activeTypeIndices.length) - 1 },
    (_, index) => index + 1
  ).sort((left, right) => popcount(left) - popcount(right) || left - right);
  for (const mask of subsetMasks) {
    const size = popcount(mask);
    if (minimumForcedSize !== null && size > minimumForcedSize) continue;
    const subset = activeTypeIndices.filter((_, index) => mask & (1 << index));
    const forbiddenPlacementKeys = subset.flatMap(index =>
      placementsByType.get(index).filter(placement => placement.key !== incoming.key).map(placement => placement.key)
    );
    const result = search({ fixedPlacements: [incoming], forbiddenPlacementKeys });
    if (result.success) {
      const verification = verifyPolycubeCoronaPatch(candidate.voxels, result.corona, 1, {
        forbiddenPlacementKeys
      });
      if (!verification.verified) {
        throw new Error(`Subset witness failed verification: ${verification.reason}`);
      }
    }
    subsetTrials.push({
      types: subset,
      forbidden_placements: forbiddenPlacementKeys.length,
      success: result.success,
      exhausted: result.exhausted,
      stopped_by: result.stopped_by,
      nodes: result.nodes
    });
    if (!result.success && !result.exhausted) {
      throw new Error(`Forced-subset test hit ${result.stopped_by} for incoming orbit ${incomingOrbit}`);
    }
    if (!result.exhausted) continue;
    if (minimumForcedSize === null) minimumForcedSize = size;
    if (size === minimumForcedSize) minimumForcedTypeSets.push(subset);
  }

  const allActiveForbidden = activeTypeIndices.flatMap(index =>
    placementsByType.get(index).filter(placement => placement.key !== incoming.key).map(placement => placement.key)
  );
  const noOutgoing = search({
    fixedPlacements: [incoming],
    forbiddenPlacementKeys: allActiveForbidden
  });
  if (!noOutgoing.success && !noOutgoing.exhausted) {
    throw new Error(`No-outgoing test hit ${noOutgoing.stopped_by} for incoming orbit ${incomingOrbit}`);
  }
  if (noOutgoing.success) {
    const verification = verifyPolycubeCoronaPatch(candidate.voxels, noOutgoing.corona, 1, {
      forbiddenPlacementKeys: allActiveForbidden
    });
    if (!verification.verified) {
      throw new Error(`No-outgoing witness failed verification: ${verification.reason}`);
    }
  }

  rows.push({
    incoming_orbit: incomingOrbit,
    incoming_type: incomingType,
    incoming_active: active.has(incomingType),
    source_active_types: [...entry.source_active_types].sort((left, right) => left - right),
    reciprocal_placements: entry.placement_keys.size,
    extendable_corona: true,
    baseline_nodes: baseline.nodes,
    possible_outgoing_types: [...possibleOutgoingTypes].sort((left, right) => left - right),
    possible_target_incoming_orbits: [...possibleOutgoingOrbits].sort((left, right) => left - right),
    possible_outgoing_placements: possibleOutgoingPlacements,
    outgoing_active_required: noOutgoing.exhausted,
    no_outgoing_trial: {
      success: noOutgoing.success,
      exhausted: noOutgoing.exhausted,
      nodes: noOutgoing.nodes
    },
    minimum_forced_disjunction_size: minimumForcedSize,
    minimum_forced_type_sets: minimumForcedTypeSets,
    subset_trials: subsetTrials
  });
}

const edges = [...possibleEdges.values()].map(edge => ({
  ...edge,
  outgoing_types: [...edge.outgoing_types].sort((left, right) => left - right)
})).sort((left, right) => left.from - right.from || left.to - right.to);

const adjacency = new Map(orbitEntries.map((_, index) => [index, []]));
for (const edge of edges) adjacency.get(edge.from).push(edge.to);
const cyclicNodes = new Set();
const visit = (start, node, seen) => {
  for (const next of adjacency.get(node)) {
    if (next === start) { cyclicNodes.add(start); return; }
    if (seen.has(next)) continue;
    visit(start, next, new Set([...seen, next]));
  }
};
for (const node of adjacency.keys()) visit(node, node, new Set([node]));

const inactiveRows = rows.filter(row => row.extendable_corona && !row.incoming_active);
const activeRows = rows.filter(row => row.extendable_corona && row.incoming_active);
const inactiveRulesOnlyRequireAnyPossibleState = inactiveRows.every(row =>
  row.outgoing_active_required
  && row.minimum_forced_type_sets.length === 1
  && row.minimum_forced_type_sets[0].join(",") === row.possible_outgoing_types.join(",")
);
const activeIncomingCanTerminate = activeRows.every(row => !row.outgoing_active_required);

process.stdout.write(`${JSON.stringify({
  type: "conditional_contact_transition_summary",
  id,
  model: "exact radius-one coronas conditioned on a reciprocal incoming contact orbit",
  active_type_indices: activeTypeIndices,
  reciprocal_incoming_orbits: orbitEntries.map((entry, index) => ({
    index,
    incoming_types: [...entry.incoming_types].sort((left, right) => left - right),
    incoming_active: [...entry.incoming_types].some(type => active.has(type)),
    source_active_types: [...entry.source_active_types].sort((left, right) => left - right),
    reciprocal_placements: entry.placement_keys.size,
    orbit_key: entry.orbit_key
  })),
  possible_transition_edges: edges,
  locally_cyclic_incoming_orbits: [...cyclicNodes].sort((left, right) => left - right),
  inactive_incoming_orbits: inactiveRows.length,
  active_incoming_orbits: activeRows.length,
  inactive_rules_only_require_any_possible_state: inactiveRulesOnlyRequireAnyPossibleState,
  active_incoming_can_terminate: activeIncomingCanTerminate,
  terminating_active_incoming_orbits: activeRows
    .filter(row => !row.outgoing_active_required)
    .map(row => row.incoming_orbit),
  conditioned_orbits: rows,
  conclusion: rows.every(row => row.extendable_corona)
    ? activeIncomingCanTerminate
      ? "Every reciprocal incoming orbit extends through radius one, but active incoming states can terminate without another active contact; this local rule does not force an unbounded chain."
      : "Every reciprocal incoming orbit extends through radius one; consult the forced transition summary."
    : "At least one reciprocal incoming orbit is locally obstructed.",
  warning: "Possible local transition cycles do not certify a compatible infinite path, periodic tiling, or aperiodicity."
})}\n`);
