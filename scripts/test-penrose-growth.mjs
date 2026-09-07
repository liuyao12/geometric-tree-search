import assert from "node:assert/strict";
import { createPenroseGrowth, growthRhomb, interiorsOverlap } from "../assets/penrose-growth.js";
import { asFive, cycloMultiply } from "../assets/cyclotomic-five.js";
import { ammannStates, solveAmmannDecorations } from "../assets/penrose-ammann.js";

import { arrowStates } from "../assets/penrose-arrows.js";

const tile = growthRhomb([0, 0, 0, 0, 0], 0, 1);
assert(interiorsOverlap(tile, tile), "identical tiles overlap");
assert(!interiorsOverlap(tile, growthRhomb([1, 0, 0, 0, 0], 0, 1)), "a shared edge is allowed");
assert(!interiorsOverlap(tile, growthRhomb([1, 1, 0, 0, 0], 0, 1)), "a shared vertex is allowed");
assert(!interiorsOverlap(tile, growthRhomb([5, 0, 0, 0, 0], 0, 1)), "separated polygons do not overlap");
const small = { ...tile, exactPoints: tile.exactPoints.map(p => asFive(cycloMultiply(p, { coeff: [-1, 0, -1, -1], denominator: 1 }))) };
assert(interiorsOverlap(tile, small), "containment must be detected without an edge crossing");

function run(useMarkings, options = {}) {
  const growth = createPenroseGrowth({ useMarkings, targetCount: 60, nodeLimit: 10000, seed: 17, ...options });
  const replay = [], events = []; let next;
  while (!(next = growth.next()).done) {
    const event = next.value; events.push(event);
    if (event.type === "add") replay.push(event.tile.id);
    if (event.type === "remove") assert.equal(replay.pop(), event.tile.id, "DFS rollback is LIFO");
  }
  const result = growth.snapshot();
  assert.deepEqual(replay, result.tiles.map(t => t.id));
  assert.equal(result.stats.proposals, events.filter(e => e.type === "try").length);
  assert.equal(result.stats.backtracks, events.filter(e => e.type === "remove").length);
  assert(result.stats.proposals <= (options.nodeLimit || 10000));
  const totals = new Map(), boundary = new Map();
  for (const tile of result.tiles) {
    tile.vertices.forEach((v, k) => totals.set(v, (totals.get(v) || 0) + tile.weights[k]));
    tile.vertices.forEach((v, k) => { const next = tile.vertices[(k + 1) % 4], key = [v, next].sort().join("|"); if (!boundary.has(key)) boundary.set(key, []); boundary.get(key).push([v, next]); });
  }
  assert([...totals.values()].every(n => n <= 10));
  for (let i = 0; i < result.tiles.length; i++) for (let j = i + 1; j < result.tiles.length; j++) assert(!interiorsOverlap(result.tiles[i], result.tiles[j]));
  const graph = new Map();
  for (const records of boundary.values()) {
    assert(records.length <= 2);
    if (records.length !== 1) continue;
    const [a, b] = records[0]; for (const [v, w] of [[a, b], [b, a]]) { if (!graph.has(v)) graph.set(v, []); graph.get(v).push(w); }
  }
  assert([...graph.values()].every(v => v.length === 2));
  const seen = new Set(), queue = [graph.keys().next().value];
  while (queue.length) { const v = queue.pop(); if (seen.has(v)) continue; seen.add(v); queue.push(...graph.get(v)); }
  assert.equal(seen.size, graph.size, "there is one boundary, with no enclosed holes");
  const arrowAssignments = new Map(result.orientations), arrowEdges = new Map();
  for (const tile of result.tiles) {
    const state = arrowStates(tile).find(s => s.start === arrowAssignments.get(tile.id)); assert(state);
    for (const [edge, signature] of state.signatures) {
      if (arrowEdges.has(edge)) assert.equal(signature, arrowEdges.get(edge)); else arrowEdges.set(edge, signature);
    }
  }
  if (useMarkings) {
    assert.equal(result.stats.edgeChecks, 0, "bar mode never invokes the edge-arrow predicate");
    assert(result.stats.markingChecks > 0);
    const assignments = new Map(result.orientations), signatures = new Map();
    for (const tile of result.tiles) {
      const state = ammannStates(tile).find(s => s.start === assignments.get(tile.id)); assert(state); assert.equal(state.bars.length, 5);
      for (const [edge, signature] of state.signatures) { if (signatures.has(edge)) assert.equal(signature, signatures.get(edge)); else signatures.set(edge, signature); }
    }
  } else { assert.equal(result.stats.markingPrunes, 0); assert.equal(result.stats.markingChecks, 0); assert(result.stats.edgeChecks > 0); assert(result.stats.edgePrunes > 0); }
  return { result, events };
}
const plain = run(false), marked = run(true);
assert.equal(plain.result.status, "target reached"); assert.equal(marked.result.status, "target reached");
assert.equal(plain.events[0].tile.id, marked.events[0].tile.id, "both lanes have exactly the same seed");
assert.equal(plain.events.find(e => e.type === "try").tile.id, marked.events.find(e => e.type === "try").tile.id);
assert(marked.result.stats.backtracks > 0); assert(marked.result.stats.markingPrunes > 0);
assert(solveAmmannDecorations(plain.result.tiles).success, "explicit edge rules must yield an Ammann-compatible patch");
assert.deepEqual(plain.events.map(e => [e.type, e.tile.id]), marked.events.map(e => [e.type, e.tile.id]), "equivalent local rules produce the same DFS path");
const limited = run(true, { nodeLimit: 100 }); assert.equal(limited.result.status, "budget reached");
const repeat = run(true, { nodeLimit: 100 });
assert.deepEqual(limited.events, repeat.events, "same seed and budget reproduce the real trace");
console.log(JSON.stringify({ ok: true, plain: plain.result.stats, marked: marked.result.stats, checked: "exact overlap, boundary, capacity, marking compatibility, shared seed, real rollback, deterministic budget stop" }));
