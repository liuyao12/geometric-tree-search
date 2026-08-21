#!/usr/bin/env node

import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import {
  enumeratePolycubeCoronaPlacements,
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
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};
const id = args.get("id") ?? "p9-42947";
const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === id);
if (!candidate) throw new Error(`Unknown polycube catalogue candidate: ${id}`);
const layers = Math.max(1, Math.floor(numberArg("layers", 1)));
const maxIterations = Math.max(1, Math.floor(numberArg("iterations", 200)));
const nodeLimit = Math.max(1, Math.floor(numberArg("nodes", 5_000_000)));
const timeLimitMs = Math.max(1, numberArg("time-ms", 30_000));
const excludeCellClauses = booleanArg("exclude-cell-clauses", true);

const catalog = enumeratePolycubeCoronaPlacements(candidate.voxels, layers);
const typeKeys = [...new Set(catalog.map(placement =>
  polycubeRootContactKey(candidate.voxels, placement)
))].sort();
const typeId = new Map(typeKeys.map((key, index) => [key, index]));
const placementsByType = typeKeys.map(() => []);
for (const placement of catalog) {
  placementsByType[typeId.get(polycubeRootContactKey(candidate.voxels, placement))]
    .push(placement.key);
}
const directions = [
  [1, 0, 0], [-1, 0, 0],
  [0, 1, 0], [0, -1, 0],
  [0, 0, 1], [0, 0, -1]
];
const rootSet = new Set(candidate.voxels.map(cell => cell.join(",")));
const targetKeys = new Set();
let frontier = new Set(rootSet);
for (let layer = 1; layer <= layers; layer++) {
  const next = new Set();
  for (const frontierKey of frontier) {
    const cell = frontierKey.split(",").map(Number);
    for (const direction of directions) {
      const key = cell.map((value, axis) => value + direction[axis]).join(",");
      if (rootSet.has(key) || targetKeys.has(key)) continue;
      targetKeys.add(key);
      next.add(key);
    }
  }
  frontier = next;
}
const cellCoverageClauses = [];
const cellCoverageSignatures = new Set();
for (const targetKey of targetKeys) {
  const clause = new Set(catalog
    .filter(placement => placement.cells.some(cell => cell.join(",") === targetKey))
    .map(placement => typeId.get(polycubeRootContactKey(candidate.voxels, placement))));
  const signature = [...clause].sort((left, right) => left - right).join(",");
  if (signature && !cellCoverageSignatures.has(signature)) {
    cellCoverageSignatures.add(signature);
    cellCoverageClauses.push(clause);
  }
}

const coronaTypeSet = corona => new Set(corona.map(placement =>
  typeId.get(polycubeRootContactKey(candidate.voxels, placement))
));
const setSignature = set => [...set].sort((left, right) => left - right).join(",");

function minimumHittingSet(sets, excludedSubsets = []) {
  const containsExcludedSubset = selected => excludedSubsets.some(subset =>
    [...subset].every(value => selected.includes(value))
  );
  const greedy = () => {
    const remaining = sets.slice();
    const selected = [];
    while (remaining.length) {
      const frequencies = new Map();
      for (const set of remaining) for (const value of set) {
        frequencies.set(value, (frequencies.get(value) ?? 0) + 1);
      }
      const choice = [...frequencies].sort((left, right) =>
        right[1] - left[1] || left[0] - right[0]
      )[0][0];
      selected.push(choice);
      for (let index = remaining.length - 1; index >= 0; index--) {
        if (remaining[index].has(choice)) remaining.splice(index, 1);
      }
    }
    return containsExcludedSubset(selected) ? null : selected;
  };

  let best = greedy();
  const search = (selected, remaining) => {
    if (!remaining.length) {
      if (!containsExcludedSubset(selected) && (!best || selected.length < best.length)) {
        best = selected.slice();
      }
      return;
    }
    if (best && selected.length >= best.length) return;
    const pivot = remaining.slice().sort((left, right) => left.size - right.size)[0];
    const frequencies = new Map();
    for (const set of remaining) for (const value of set) {
      frequencies.set(value, (frequencies.get(value) ?? 0) + 1);
    }
    for (const value of [...pivot].sort((left, right) =>
      (frequencies.get(right) ?? 0) - (frequencies.get(left) ?? 0) || left - right
    )) {
      search([...selected, value], remaining.filter(set => !set.has(value)));
    }
  };
  search([], sets);
  return best?.sort((left, right) => left - right) ?? null;
}

const hittingSetSelfTest = minimumHittingSet([
  new Set([0, 1]),
  new Set([1, 2])
]);
const excludedHittingSetSelfTest = minimumHittingSet([
  new Set([0, 1]),
  new Set([1, 2])
], [new Set([1])]);
if (hittingSetSelfTest.join(",") !== "1"
  || excludedHittingSetSelfTest.join(",") !== "0,2") {
  throw new Error("Minimum hitting-set self-test failed");
}

const baseline = searchPolycubeCorona(candidate.voxels, {
  layers,
  nodeLimit,
  timeLimitMs
});
if (!baseline.success) throw new Error("Unable to obtain a baseline corona");
const constraints = [coronaTypeSet(baseline.corona)];
const signatures = new Set(constraints.map(setSignature));
const iterations = [];

for (let iteration = 0; iteration < maxIterations; iteration++) {
  const hittingSet = minimumHittingSet(
    constraints,
    excludeCellClauses ? cellCoverageClauses : []
  );
  if (!hittingSet) {
    iterations.push({
      iteration: iteration + 1,
      corona_constraints: constraints.length,
      outcome: "no_nontrivial_hitting_set"
    });
    break;
  }
  const forbiddenPlacementKeys = hittingSet.flatMap(index => placementsByType[index]);
  const result = searchPolycubeCorona(candidate.voxels, {
    layers,
    seed: iteration,
    forbiddenPlacementKeys,
    nodeLimit,
    timeLimitMs
  });
  const row = {
    iteration: iteration + 1,
    corona_constraints: constraints.length,
    hitting_set_size: hittingSet.length,
    hitting_type_indices: hittingSet,
    forbidden_placements: forbiddenPlacementKeys.length,
    outcome: result.success
      ? "counterexample"
      : result.exhausted
        ? "forced_disjunction"
        : "incomplete",
    nodes: result.nodes,
    milliseconds: result.milliseconds,
    stopped_by: result.stopped_by
  };
  iterations.push(row);
  if (!result.success) break;
  const verification = verifyPolycubeCoronaPatch(candidate.voxels, result.corona, layers, {
    forbiddenPlacementKeys
  });
  if (!verification.verified) {
    throw new Error(`Counterexample failed independent verification: ${verification.reason}`);
  }
  const counterexample = coronaTypeSet(result.corona);
  const signature = setSignature(counterexample);
  if (signatures.has(signature)) {
    row.outcome = "duplicate_counterexample";
    break;
  }
  signatures.add(signature);
  constraints.push(counterexample);
}

const final = iterations.at(-1);
const replaySeeds = [0, 1, 2, 3, 4, 5, 6, 7];
const finalHittingSet = final?.hitting_type_indices ?? [];
const finalForbiddenPlacementKeys = finalHittingSet.flatMap(index => placementsByType[index]);
const replay = final?.outcome === "forced_disjunction"
  ? replaySeeds.map(seed => {
      const result = searchPolycubeCorona(candidate.voxels, {
        layers,
        seed,
        forbiddenPlacementKeys: finalForbiddenPlacementKeys,
        nodeLimit,
        timeLimitMs
      });
      if (!result.exhausted) {
        throw new Error(`Forced disjunction failed replay at seed ${seed}`);
      }
      return {
        seed,
        exhausted: true,
        nodes: result.nodes,
        failed_states: result.failed_states,
        milliseconds: result.milliseconds
      };
    })
  : [];
process.stdout.write(`${JSON.stringify({
  type: "contact_disjunction_summary",
  id,
  layers,
  model: "root-contact types canonicalized under the proper rotational stabilizer",
  catalog_placements: catalog.length,
  contact_types: typeKeys.length,
  single_cell_coverage_clauses: cellCoverageClauses.length,
  excluded_single_cell_clauses: excludeCellClauses,
  counterexample_coronas: constraints.length,
  classification: final?.outcome ?? "no_iterations",
  final_hitting_set_size: final?.hitting_set_size ?? null,
  final_hitting_type_indices: finalHittingSet,
  final_hitting_types: finalHittingSet.map(index => ({
    index,
    contact_key: typeKeys[index],
    placements: placementsByType[index].length
  })),
  final_forbidden_placements: finalForbiddenPlacementKeys.length,
  minimum_nontrivial: final?.outcome === "forced_disjunction" && excludeCellClauses,
  replay,
  iterations,
  warning: "A radius-one forced contact disjunction is only a local rule, not a tiling or aperiodicity proof."
})}\n`);
