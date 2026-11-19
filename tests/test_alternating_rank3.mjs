import assert from 'node:assert/strict';
import {A2_TILE_LOOPS, FixedA2Marking, tileOrientations, a2InverseTransform} from '../assets/a2-tiling-engine.js';
import {TILE_SETS, parity} from '../assets/tile-corona-learning.js';
import {createAlternatingMarking, createHatRank3Marking, hatKagomeValues, HAT_RANK3_MAX_EXTENT} from '../assets/hat-rank3-marking.js';
import {markingSegmentEndpoints} from '../assets/marking-segments.js';

const root = tile => ({tile, orientation: tileOrientations(tile, A2_TILE_LOOPS[tile])[0], translation: [0,0,0]});
const hat = root('hat');
// These two legal Turtle contacts demanded opposite signs with the constant
// Turtle coloring. Both agree with the fully assigned Hat under alternation.
const mixed = createAlternatingMarking(['hat', 'turtle']);
const shared = '3,3,-6|1';
const core = mixed.entries(hat);
assert.deepEqual(core, createHatRank3Marking({extent: 0, pattern: 'more'}).entries(hat));
assert.equal(core.size, 72);
assert.equal(core.get(shared), -1);
mixed.push(hat);
for (const [index, translation] of [[3, [3,3,-6]], [9, [5,5,-10]]]) {
  const contact = {tile: 'turtle', orientation: tileOrientations('turtle', A2_TILE_LOOPS.turtle)[index], translation};
  assert.equal(mixed.compatible(contact), true);
  assert.equal(mixed.entries(contact).get(shared), core.get(shared));
  mixed.push(contact);
  assert.equal(mixed.contacts.get(shared).count, 2);
  mixed.pop(contact);
  assert.equal(mixed.contacts.get(shared).count, 1);
}
// Every nonzero component flips at the next occupied site in its own direction.
for (const tile of ['hat', 'turtle']) {
  const entries = mixed.entries(root(tile));
  const checked = new Set();
  for (const [key, value] of entries) {
    if (!value) continue;
    const [xyz, c] = key.split('|'), component = Number(c);
    const next = xyz.split(',').map((v, i) => Number(v) + (i === component ? -2 : 1));
    const neighbor = entries.get(next.join(',') + '|' + c);
    if (neighbor === undefined) continue;
    assert.equal(neighbor, -value);
    checked.add(component);
  }
  assert.equal(checked.size, 3);
}

// Enumerate complete point stars using geometry alone. Every tile of a star
// covers the origin, so anchoring each of its occupied sites there is exhaustive.
// Distinguish an identity-oriented seed and compare every contributed component.
function verifyStars(setId) {
  const {tiles, allowReflections} = TILE_SETS[setId];
  const rule = createAlternatingMarking(tiles);
  const candidates = [];
  for (const tile of tiles) {
    for (const orientation of tileOrientations(tile, A2_TILE_LOOPS[tile])) {
      if (!allowReflections && parity(orientation.symmetry.permutation) < 0) continue;
      for (const {point: anchor, weight} of orientation.occupancy.values()) {
        const translation = anchor.map(n => -n);
        const occupancy = [...orientation.occupancy.values()].map(({point, weight}) =>
          [point.map((n, i) => n + translation[i]).join(','), weight]);
        const entries = rule.entries({tile, orientation, translation});
        const signs = [0, 1, 2].map(c => entries.get('0,0,0|' + c));
        // Six is a period in each axial coordinate. Equality of these tables
        // proves equality of the transported fields at every lattice site.
        const {symmetry} = orientation;
        const phase = [];
        for (let x = 0; x < 6; x++) for (let y = 0; y < 6; y++) {
          const q = [x,y,-x-y].map((v,j) => v-translation[j]);
          const local = hatKagomeValues(a2InverseTransform(q,symmetry)) ?? [0,0,0];
          phase.push(...symmetry.permutation.map(c => parity(symmetry.permutation)*local[c]));
        }
        const phaseSign = setId === 'turtle' ? -1 : 1;
        assert.ok(setId === 'turtle' ? signs.some(v => v !== undefined) : signs.every(v => v !== undefined));
        assert.ok(signs.every((v,c) => v === undefined || v === phaseSign * phase[c]));
        candidates.push({identity: orientation.index === 0, weight, occupancy, phase: phase.join(',')});
      }
    }
  }
  let count = 0;
  for (const seed of candidates.filter(c => c.identity)) {
    function fill(start, remaining, sums, star) {
      if (remaining === 0) {
        for (const tile of star) {
          assert.equal(tile.phase, seed.phase);
        }
        count++;
        return;
      }
      for (let i = start; i < candidates.length; i++) {
        const tile = candidates[i];
        if (tile === seed || tile.weight > remaining) continue;
        if (tile.occupancy.some(([p, w]) => (sums.get(p) ?? 0) + w > 12)) continue;
        const next = new Map(sums);
        for (const [p, w] of tile.occupancy) next.set(p, (next.get(p) ?? 0) + w);
        fill(i + 1, remaining - tile.weight, next, [...star, tile]);
      }
    }
    fill(0, 12 - seed.weight, new Map(seed.occupancy), []);
  }
  return count;
}
assert.equal(verifyStars('turtle'), 200);
assert.equal(verifyStars('hat'), 196);
assert.equal(verifyStars('mixed'), 376);
// Use the outline endpoints to reconstruct the new (site, direction) pairs
// independently. A site reached by two stripe ends acquires both components.
const stripeVertices = {
  hat: [[0,6],[2,10],[4,12],[8,10]],
  turtle: [[0,10],[2,8],[0,6],[4,12]]
};
for (const tile of ['hat','turtle']) {
  const loop = A2_TILE_LOOPS[tile];
  const expected = new Map(mixed.entries(root(tile)));
  for (let extent = 1; extent <= HAT_RANK3_MAX_EXTENT; extent++) {
    for (const [a,b] of stripeVertices[tile]) {
      const delta = loop[b].map((v,i) => v - loop[a][i]);
      const length = Math.min(...delta.map(Math.abs));
      const step = delta.map(v => v / length);
      const component = step.findIndex(v => Math.abs(v) === 2);
      for (const [end, sign] of [[a,-1],[b,1]]) {
        const p = loop[end].map((v,i) => v - loop[0][i] + sign * extent * step[i]);
        const value = hatKagomeValues(p)[component];
        assert.equal(Math.abs(value),1);
        expected.set(p.join(',') + '|' + component,value);
      }
    }
    assert.deepEqual(createAlternatingMarking(['hat','turtle'],extent).entries(root(tile)),expected);
    if (tile==='hat') {
      assert.deepEqual(createAlternatingMarking(['hat'],extent).entries(hat),expected);
      assert.deepEqual(createHatRank3Marking({extent,pattern:'more'}).entries(hat),expected);
      const reversed = new Map([...expected].map(([k,v]) => [k,v===0?0:-v]));
      assert.deepEqual(createHatRank3Marking({extent,pattern:'alternate'}).entries(hat),reversed);
    }
  }
}

// Compare every (point, component), including zeros, in every orientation.
// Walk both ends and the entire original stripe to check the phase independently.
const turtles = tileOrientations('turtle',A2_TILE_LOOPS.turtle);
for (let extent = 0; extent <= HAT_RANK3_MAX_EXTENT; extent++) {
  const constant = new FixedA2Marking(extent,{tiles:['turtle'],rank:3});
  const alternating = createAlternatingMarking(['turtle'],extent);
  for (const orientation of turtles) {
    const placement = {tile:'turtle',orientation,translation:[3,-1,-2]};
    const c = constant.entries(placement), a = alternating.entries(placement);
    assert.deepEqual(new Map([...a].map(([key,v]) => [key,Math.abs(v)])),
                     new Map([...c].map(([key,v]) => [key,Math.abs(v)])));
    for (const {fromPoint,toPoint,value} of constant.segments(placement)) {
      const delta = toPoint.map((v,i) => v - fromPoint[i]);
      const length = Math.min(...delta.map(Math.abs));
      const step = delta.map(v => v / length);
      const component = step.findIndex(v => Math.abs(v) === 2);
      for (let k = -extent; k <= length + extent; k++) {
        const point = fromPoint.map((v,i) => v + k * step[i]);
        const key = point.join(',') + '|' + component;
        assert.equal(c.get(key),value);
        assert.equal(a.get(key),k % 2 === 0 ? value : -value);
      }
    }
  }
}
for(let c=0;c<3;c++) {
  const p=[0,0,0], q=p.map((v,i)=>i===c?-2:1);
  assert.deepEqual(markingSegmentEndpoints({point:p,component:c})[1],markingSegmentEndpoints({point:q,component:c})[0]);
}
console.log('Every complete rooted point star shares one periodic field: 200 Turtle, 196 Hat, 376 mixed. Extents and midpoint joins passed.');
