import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { A2_TILE_LOOPS, FixedTurtleMarking, NoA2Marking, a2Transform,
  makeHexBoundary, solveA2Tiling, tileOrientations }
  from '../assets/a2-tiling-engine.js';

globalThis.requestAnimationFrame = callback => setImmediate(callback);
const orientation = tileOrientations('turtle', A2_TILE_LOOPS.turtle)[1];
const seed = {
  loop: A2_TILE_LOOPS.turtle.map(point => a2Transform(point, orientation.symmetry)),
  markingPlacement: { tile: 'turtle', orientation,
    translation: a2Transform(A2_TILE_LOOPS.turtle[0], orientation.symmetry) }
};
const sublattice = p => (p[0] - p[1]) % 3 === 0 && (p[1] - p[2]) % 3 === 0;
let checked = 0, backtracks = 0, touched = 0, rescanned = 0;
const occupancyCache = new WeakMap();
function polygonOccupancy(loop) {
  if (!occupancyCache.has(loop)) {
    const identity = tileOrientations('oracle', loop)[0];
    occupancyCache.set(loop, new Map([...identity.occupancy.values()].map(entry => {
      const point = entry.point.map((v, i) => v + loop[0][i]);
      return [point.join(','), { point, weight: entry.weight }];
    })));
  }
  return occupancyCache.get(loop);
}

// Independent whole-patch oracle, deliberately not using the solver's counts.
function oracle(event, options) {
  const points = new Map();
  const add = (occupancy, generation) => {
    for (const [key, entry] of occupancy) {
      const prior = points.get(key) || { value: 0, generation: Infinity, point: entry.point };
      prior.value += entry.weight;
      prior.generation = Math.min(prior.generation, generation);
      points.set(key, prior);
    }
  };
  if (options.seed) add(new Map([...polygonOccupancy(options.seed.loop)].filter(([, entry]) =>
    !options.latticePointFilter || options.latticePointFilter(entry.point.map((v, i) => v - options.seed.loop[0][i])))), 0);
  for (const placement of event.placements) { add(placement.occupancy, placement.generation); rescanned += placement.occupancy.size; }
  for (const point of options.startPoints || []) {
    const key = point.join(',');
    points.set(key, { point, value: points.get(key)?.value || 0, generation: 0 });
  }
  const desired = options.maximize ? null : polygonOccupancy(options.boundary);
  const generations = [...points.values()].filter(entry =>
    (entry.value > 1e-7 || options.startPoints?.some(p => p.join(',') === entry.point.join(','))) &&
    entry.value < (options.maximize ? options.pointTarget?.(entry.point) ?? 12 : desired.get(entry.point.join(','))?.weight ?? -Infinity) - 1e-7
  ).map(entry => entry.generation);
  return generations.length ? Math.min(...generations) : null;
}

async function run(label, overrides = {}) {
  const options = { boundary: makeHexBoundary(20), seed, tiles: ['turtle'], maximize: true,
    targetPlacements: 65, nodeLimit: 160, randomSeed: 10, marking: new NoA2Marking(), ...overrides };
  const events = [];
  const result = await solveA2Tiling({ ...options, onEvent: event => {
    assert.equal(event.minimumFrontierGeneration, oracle(event, options), `${label}: ${event.type} at node ${event.nodes}`);
    if (event.type === 'backtrack') backtracks++;
    checked++;
    events.push([event.type, event.minimumFrontierGeneration]);
  }});
  touched += result.stats.frontierGenerationPointUpdates;
  if (result.result === 'yes') assert.equal(result.stats.frontierGenerationFullBuilds, 1, `${label}: no full rebuild during normal growth`);
  console.log(`${label}: ${result.result}, ${result.stats.nodes} placements, ${result.stats.backtracks} backtracks, ${events.length} snapshots`);
  return { result, events };
}

for (const rank of [1, 3]) for (const latticePointFilter of [null, sublattice]) {
  const label = `rank ${rank}, ${latticePointFilter ? 'sublattice' : 'full lattice'}`;
  const first = await run(label, { latticePointFilter, marking: new FixedTurtleMarking(1, { rank, pointFilter: latticePointFilter }) });
  await run(`${label}, resume`, { latticePointFilter, initialPlacements: first.result.placements.slice(0, 8),
    targetPlacements: 18, marking: new FixedTurtleMarking(1, { rank, pointFilter: latticePointFilter }) });
}
await run('unmarked backtracking', { randomSeed: 4, targetPlacements: 500 });
await run('finite completed frontier', { boundary: A2_TILE_LOOPS.turtle, seed: null, maximize: false });
await run('empty frontier', { seed: null, targetPlacements: 0 });
await run('start-point frontier', { seed: null, startPoints: [[0, 0, 0]], targetPlacements: 5 });
assert.ok(backtracks > 0, 'must check rollback snapshots, not only forward growth');
assert.ok(rescanned > touched * 5, 'incremental maintenance must touch substantially fewer points than rebuilding every snapshot');

// Both pause consumers use event-time snapshots, including buffered forced moves.
const html = readFileSync(new URL('../GCTS-I.html', import.meta.url), 'utf8');
assert.doesNotMatch(html, /minimumFrontierGeneration\(/);
assert.match(html, /const generation = accepted\.minimumFrontierGeneration/);
assert.match(html, /const frontierGeneration = event\.minimumFrontierGeneration/);
assert.match(html, /generation >= 3 && generation % 2 === 1 && generation > highestPausedCorona/);
console.log(`Verified ${checked} snapshots; ${backtracks} rollback snapshots; ${touched} local point updates versus ${rescanned} whole-patch visits.`);
