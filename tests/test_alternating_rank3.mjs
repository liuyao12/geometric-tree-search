import assert from 'node:assert/strict';
import {A2_TILE_LOOPS, tileOrientations} from '../assets/a2-tiling-engine.js';
import {TILE_SETS, parity} from '../assets/tile-corona-learning.js';
import {createAlternatingCoreMarking, createHatRank3Marking} from '../assets/hat-rank3-marking.js';

const root = tile => ({tile, orientation: tileOrientations(tile, A2_TILE_LOOPS[tile])[0], translation: [0,0,0]});
const hat = root('hat');
// These two legal Turtle contacts demanded opposite signs with the constant
// Turtle coloring. Both agree with the fully assigned Hat under alternation.
const mixed = createAlternatingCoreMarking(['hat', 'turtle']);
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
  const rule = createAlternatingCoreMarking(tiles);
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
        assert.ok(signs.every(v => [-1, 0, 1].includes(v)));
        candidates.push({identity: orientation.index === 0, weight, occupancy, signs});
      }
    }
  }
  let count = 0;
  for (const seed of candidates.filter(c => c.identity)) {
    function fill(start, remaining, sums, star) {
      if (remaining === 0) {
        for (const tile of star) assert.ok(tile.signs.every((v, c) => v === seed.signs[c]));
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
assert.equal(verifyStars('mixed'), 376);
console.log('All three alternating components agree on 200 Turtle and 376 mixed rooted point stars.');
