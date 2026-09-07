import assert from "node:assert/strict";
import { makeCyclotomicSearch } from "../assets/penrose-model-set.js";
import { ammannPrototype, ammannStates, solveAmmannDecorations, exactlyPerpendicular } from "../assets/penrose-ammann.js";
import { canonical, cycloAdd, cycloMultiply, latticeKey, starMap } from "../assets/cyclotomic-five.js";
const conj = a => starMap(starMap(a));
const sub = (a, b) => cycloAdd(a, { ...canonical(b), coeff: canonical(b).coeff.map(n => -n) });
const segmentKey = bar => [latticeKey(bar.from), latticeKey(bar.to)].sort().join("|");

// Independent congruence audit: map a single prototype to each placed tile
// by z -> translation + unit*z or translation + unit*conjugate(z), then
// compare every endpoint. Equal stripe counts alone would not suffice.
function assertRigidCopy(tile, state) {
  const prototype = ammannPrototype(tile.kind), original = ammannStates(prototype)[0];
  const source = Array.from({ length: 4 }, (_, k) => prototype.exactPoints[(original.start + k) % 4]);
  const target = Array.from({ length: 4 }, (_, k) => tile.exactPoints[(state.start + k) % 4]);
  let transform;
  for (const reflect of [false, true]) {
    const f = reflect ? conj : z => z;
    const u = f(sub(source[1], source[0])), v = sub(target[1], target[0]);
    const rotation = cycloMultiply(v, conj(u));
    const trial = p => cycloAdd(target[0], cycloMultiply(rotation, f(sub(p, source[0]))));
    if (source.every((p, i) => latticeKey(trial(p)) === latticeKey(target[i]))) { transform = trial; break; }
  }
  assert(transform, "tile must be a rigid copy of its prototile");
  assert.deepEqual(state.bars.map(segmentKey).sort(), original.bars.map(bar => segmentKey({ from: transform(bar.from), to: transform(bar.to) })).sort(), "all five stripes must be transformed together");
}
let tilesChecked = 0, edgesChecked = 0, markingPrunes = 0;
for (const phaseCode of [0, 47, 170, 419, 1000]) {
  const search = makeCyclotomicSearch({ targetCount: phaseCode === 170 ? 420 : 120, phaseCode });
  assert(search.success); const audit = search.model.ammann;
  assert(audit.success); assert.equal(audit.templates, 2); assert.equal(audit.families, 5);
  assert(search.stats.markingPrunes > 0);
  assert.equal(search.stats.markingPrunes, search.trace.filter(e => e.type === "reject" && e.message.startsWith("GCTS marking prune:")).length);
  const signatures = new Map();
  for (const tile of search.solution) {
    const states = ammannStates(tile);
    assert.equal(states.length, 2);
    for (const state of states) { assert.equal(state.bars.length, 5); assertRigidCopy(tile, state); }
    const state = states.find(s => s.start === audit.orientationByTile.get(tile.id));
    assert.equal(audit.byTile.get(tile.id).length, 5, "even boundary tiles retain their whole decoration");
    for (const bar of state.bars) {
      const axis = { coeff: Array.from({ length: 5 }, (_, k) => Number(k === bar.family)), denominator: 1 };
      assert(exactlyPerpendicular(sub(bar.to, bar.from), axis));
    }
    for (const [edge, signature] of state.signatures) {
      if (signatures.has(edge)) { assert.equal(signature, signatures.get(edge)); edgesChecked++; }
      else signatures.set(edge, signature);
    }
  }
  // A single boundary-only rhomb must still have exactly five stripes.
  const singleton = solveAmmannDecorations(search.solution.slice(0, 1));
  assert.equal(singleton.segments, 5); assert.equal(singleton.boundaryEndpoints, 10);
  tilesChecked += search.solution.length; markingPrunes += search.stats.markingPrunes;
}
console.log(`ok: ${tilesChecked} tiles are exact rigid copies of 2 fixed striped prototiles; ${edgesChecked} shared edges match; ${markingPrunes} proposals pruned by the markings`);
