import { iceGeometrySha256Ascii } from "./ice-molecular-anchor-growth.js?v=20260831-406";

const ICE_IH_A_ANGSTROM = 4.518;
const ICE_IH_C_ANGSTROM = 7.357;
const ICE_IH_U = 3 / 8;
const PAULING_STATES_PER_MOLECULE = 1.5;
const MAXIMUM_INTERACTIVE_PERIODIC_MOLECULES = 16;
const IMAGE_SHIFTS = [-1, 0, 1];

const primitive = [
  [ICE_IH_A_ANGSTROM, 0, 0],
  [-ICE_IH_A_ANGSTROM / 2, Math.sqrt(3) * ICE_IH_A_ANGSTROM / 2, 0],
  [0, 0, ICE_IH_C_ANGSTROM],
];
const basis = [[0, 0, 0], [2 / 3, 1 / 3, .5], [0, 0, ICE_IH_U], [2 / 3, 1 / 3, .5 + ICE_IH_U]];

const lexical = (left, right) => {
  for (let index = 0; index < Math.min(left.length, right.length); index++) {
    if (left[index] !== right[index]) return left[index] < right[index] ? -1 : 1;
  }
  return left.length - right.length;
};
const chooseTwo = (items) => items.flatMap((first, index) => items.slice(index + 1).map((second) => [first, second]));

function cartesian(address) {
  const [i, j, k, basisIndex] = address;
  const fractional = [i + basis[basisIndex][0], j + basis[basisIndex][1], k + basis[basisIndex][2]];
  return [0, 1, 2].map((axis) => fractional.reduce((sum, value, component) =>
    sum + value * primitive[component][axis], 0));
}

export function derivePeriodicIceIhOxygenGraph(repeats) {
  if (!Array.isArray(repeats) || repeats.length !== 3
    || repeats.some((value) => !Number.isInteger(value) || value < 1)) {
    throw new Error("periodic ice-Ih repeats must be three positive integers");
  }
  const addresses = [];
  for (let i = 0; i < repeats[0]; i++) for (let j = 0; j < repeats[1]; j++) {
    for (let k = 0; k < repeats[2]; k++) for (let basisIndex = 0; basisIndex < basis.length; basisIndex++) {
      addresses.push([i, j, k, basisIndex]);
    }
  }
  const positions = addresses.map(cartesian);
  const edgeByKey = new Map();
  const incident = addresses.map(() => []);
  addresses.forEach((address, first) => {
    const candidates = [];
    addresses.forEach((otherAddress, second) => IMAGE_SHIFTS.forEach((shiftI) =>
      IMAGE_SHIFTS.forEach((shiftJ) => IMAGE_SHIFTS.forEach((shiftK) => {
        if (first === second && shiftI === 0 && shiftJ === 0 && shiftK === 0) return;
        const imageShift = [shiftI, shiftJ, shiftK];
        const imageAddress = [otherAddress[0] + shiftI * repeats[0],
          otherAddress[1] + shiftJ * repeats[1], otherAddress[2] + shiftK * repeats[2], otherAddress[3]];
        const image = cartesian(imageAddress);
        const squaredDistance = image.reduce((sum, value, axis) => sum + (value - positions[first][axis]) ** 2, 0);
        candidates.push({ second, imageShift, squaredDistance });
      }))));
    candidates.sort((left, right) => left.squaredDistance - right.squaredDistance
      || left.second - right.second || lexical(left.imageShift, right.imageShift));
    const shell = candidates.slice(0, 4);
    if (shell.length !== 4 || candidates[4].squaredDistance - shell[3].squaredDistance < 1e-6) {
      throw new Error("periodic oxygen first shell is not an isolated tetrahedral shell");
    }
    shell.forEach(({ second, imageShift, squaredDistance }) => {
      const forward = [first, second, ...imageShift];
      const reverse = [second, first, ...imageShift.map((value) => -value)];
      const canonical = lexical(forward, reverse) <= 0 ? forward : reverse;
      const key = canonical.join(":");
      if (!edgeByKey.has(key)) edgeByKey.set(key, { first: canonical[0], second: canonical[1],
        imageShift: canonical.slice(2), squaredDistance });
    });
  });
  const edges = [...edgeByKey.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([key, edge], edgeIndex) => ({ edgeIndex, key, ...edge }));
  edges.forEach((edge) => { incident[edge.first].push(edge.edgeIndex); incident[edge.second].push(edge.edgeIndex); });
  if (edges.length !== 2 * addresses.length || incident.some((ports) => ports.length !== 4
    || new Set(ports).size !== 4)) throw new Error("periodic oxygen graph is not four-regular");
  const pairMultiplicity = new Map();
  edges.forEach(({ first, second }) => {
    const key = first < second ? `${first}:${second}` : `${second}:${first}`;
    pairMultiplicity.set(key, (pairMultiplicity.get(key) || 0) + 1);
  });
  const canonical = {
    repeats: [...repeats],
    latticeAngstrom: { a: ICE_IH_A_ANGSTROM, c: ICE_IH_C_ANGSTROM, u: ICE_IH_U },
    addresses,
    edges: edges.map(({ first, second, imageShift, squaredDistance }) =>
      [first, second, ...imageShift, Math.round(squaredDistance * 1e9)]),
  };
  const nearestNeighborDistanceAngstrom = Math.sqrt(Math.min(...edges.map((edge) => edge.squaredDistance)));
  return {
    addresses,
    positions,
    edges,
    incident,
    graphSha256: iceGeometrySha256Ascii(JSON.stringify(canonical)),
    parallelPeriodicEdges: [...pairMultiplicity.values()].reduce((sum, count) => sum + Math.max(0, count - 1), 0),
    nearestNeighborDistanceAngstrom,
    maximumNeighborDistanceResidualAngstrom: Math.max(...edges.map((edge) =>
      Math.abs(Math.sqrt(edge.squaredDistance) - nearestNeighborDistanceAngstrom))),
  };
}

function exactTwoDonorCount(graph) {
  const domains = graph.incident.map((ports) => chooseTwo(ports));
  if (domains.some((domain) => domain.length !== 6)) throw new Error("a tetrahedral H2O domain must have six two-donor states");
  let factors = domains.map((domain, variable) => ({ vars: [variable],
    table: new Map(domain.map((_, state) => [String(state), 1n])) }));
  graph.edges.forEach((edge) => {
    const table = new Map();
    domains[edge.first].forEach((firstState, first) => domains[edge.second].forEach((secondState, second) => {
      if (firstState.includes(edge.edgeIndex) !== secondState.includes(edge.edgeIndex)) {
        table.set(`${first},${second}`, 1n);
      }
    }));
    factors.push({ vars: [edge.first, edge.second], table });
  });
  const remaining = new Set(domains.map((_, index) => index));
  let maximumEliminationScope = 0;
  const factorValue = (factor, assignment) => factor.table.get(
    factor.vars.map((variable) => assignment.get(variable)).join(",")) || 0n;
  while (remaining.size) {
    const variable = [...remaining].map((candidate) => {
      const neighbors = new Set(factors.filter((factor) => factor.vars.includes(candidate))
        .flatMap((factor) => factor.vars.filter((other) => other !== candidate && remaining.has(other))));
      const list = [...neighbors]; let fill = 0;
      for (let first = 0; first < list.length; first++) for (let second = first + 1; second < list.length; second++) {
        if (!factors.some((factor) => factor.vars.includes(list[first]) && factor.vars.includes(list[second]))) fill++;
      }
      return { candidate, fill, degree: neighbors.size };
    }).sort((left, right) => left.fill - right.fill || left.degree - right.degree
      || left.candidate - right.candidate)[0].candidate;
    const bucket = factors.filter((factor) => factor.vars.includes(variable));
    factors = factors.filter((factor) => !factor.vars.includes(variable));
    const scope = [...new Set(bucket.flatMap((factor) => factor.vars))].sort((first, second) => first - second);
    const outputVars = scope.filter((item) => item !== variable);
    maximumEliminationScope = Math.max(maximumEliminationScope, scope.length);
    const table = new Map(); const assignment = new Map();
    const visit = (depth) => {
      if (depth < scope.length) {
        const current = scope[depth];
        for (let state = 0; state < domains[current].length; state++) {
          assignment.set(current, state); visit(depth + 1);
        }
        assignment.delete(current); return;
      }
      const value = bucket.reduce((product, factor) => product * factorValue(factor, assignment), 1n);
      if (!value) return;
      const key = outputVars.map((item) => assignment.get(item)).join(",");
      table.set(key, (table.get(key) || 0n) + value);
    };
    visit(0);
    factors.push({ vars: outputVars, table }); remaining.delete(variable);
  }
  return {
    exactAssignmentCount: factors.reduce((product, factor) => product * (factor.table.get("") || 0n), 1n),
    maximumEliminationScope,
  };
}

export function buildPeriodicIceIhBoundaryAudit(repeats) {
  const graph = derivePeriodicIceIhOxygenGraph(repeats);
  if (graph.addresses.length > MAXIMUM_INTERACTIVE_PERIODIC_MOLECULES) {
    throw new Error(`periodic exact counter is capped at ${MAXIMUM_INTERACTIVE_PERIODIC_MOLECULES} molecules for interactive use`);
  }
  const counted = exactTwoDonorCount(graph);
  const moleculeCount = graph.addresses.length;
  const countText = counted.exactAssignmentCount.toString();
  const logAssignmentCount = countText.length < 16 ? Math.log(Number(counted.exactAssignmentCount))
    : Math.log(Number(countText.slice(0, 15))) + (countText.length - 15) * Math.log(10);
  return {
    schema: "gcts-periodic-ice-ih-boundary-audit-v1",
    repeats: [...repeats],
    moleculeCount,
    oxygenConnections: graph.edges.length,
    exactAssignmentCount: counted.exactAssignmentCount.toString(),
    logAssignmentCount,
    logAssignmentsPerMolecule: logAssignmentCount / moleculeCount,
    paulingReferenceLogAssignmentsPerMolecule: Math.log(PAULING_STATES_PER_MOLECULE),
    graphSha256: graph.graphSha256,
    parallelPeriodicEdges: graph.parallelPeriodicEdges,
    nearestNeighborDistanceAngstrom: graph.nearestNeighborDistanceAngstrom,
    maximumNeighborDistanceResidualAngstrom: graph.maximumNeighborDistanceResidualAngstrom,
    maximumEliminationScope: counted.maximumEliminationScope,
    maximumInteractiveMolecules: MAXIMUM_INTERACTIVE_PERIODIC_MOLECULES,
    oxygenGraphDerivedFromDeclaredLatticeGeometry: true,
    everyOxygenFourConnected: true,
    everyMoleculeDonatesTwice: true,
    everyConnectionHasExactlyOneProton: true,
    periodicBoundary: true,
    openBoundary: false,
    protonCoordinatesUsed: false,
    targetUsed: false,
    physicalPotentialUsed: false,
    thermodynamicEntropyInferred: false,
    bulkLimitClaimed: false,
    claimBoundary: "Exact two-donor/one-proton counting on one finite periodic Ice-Ih oxygen supercell. It is a geometry-derived finite-size reference, not a bulk-limit extrapolation, energy-weighted ensemble, measured residual entropy, or proton-growth mechanism.",
  };
}

export function buildPeriodicIceIhBoundarySeries() {
  return [[1, 1, 1], [2, 1, 1], [3, 1, 1], [2, 2, 1]].map(buildPeriodicIceIhBoundaryAudit);
}
