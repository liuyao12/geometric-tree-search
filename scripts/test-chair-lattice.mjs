import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { VARIANTS, FACE_DIRECTIONS, ROTATIONS, apply, add, key, chairLeaves } from '../3d-reptiles/chair/chair44.js';
import { LATTICE_MODEL, latticeTile, scalarPanelMark, verifyLatticePatch } from '../3d-reptiles/chair/chair-lattice.js';

const signature = entries => entries.map(({ point, value }) => `${key(point)}:${value}`).sort();
assert.equal(LATTICE_MODEL.t.length, 7);
assert.equal(LATTICE_MODEL.m.length, 288);
assert.equal(new Set(LATTICE_MODEL.m.map(entry => key(entry.point))).size, 288);
assert.deepEqual(new Set(LATTICE_MODEL.m.map(entry => entry.value)), new Set([-1, 0, 1]));
assert.deepEqual(JSON.parse(readFileSync(new URL('../3d-reptiles/chair/chair44-lattice.json', import.meta.url))), LATTICE_MODEL);

// Pure pullback: rotating points alone must reproduce every oriented prototype.
for (const [variantId, rotation] of ROTATIONS.entries()) {
  const origin = [-3, 2, 5], tile = latticeTile({ variantId, origin });
  for (const channel of ['t', 'm']) {
    const transformed = LATTICE_MODEL[channel].map(({ point, value }) => ({
      point: apply(rotation, point.map(v => v - 12)).map((v, i) => v + 12 + 12 * origin[i]), value,
    }));
    assert.deepEqual(signature(tile[channel]), signature(transformed));
  }
}

// All facing normal/direction/color combinations, including assigned blue zeros.
let panelCases = 0;
for (const normal of FACE_DIRECTIONS) {
  const axis = normal.findIndex(v => v !== 0);
  const arrows = [-1, 1].flatMap(a => [-1, 1].map(b => {
    const values = [a, b]; return normal.map((_, i) => i === axis ? 0 : values.shift());
  }));
  for (const a of arrows) for (const b of arrows) for (const left of ['red', 'green', 'blue']) for (const right of ['red', 'green', 'blue']) {
    const first = scalarPanelMark({ cell: [0, 0, 0], direction: normal, arrow: a, color: left });
    const second = scalarPanelMark({ cell: normal, direction: normal.map(v => -v), arrow: b, color: right });
    const expected = key(a) === key(b) && ((left === 'blue' && right === 'blue') || (left === 'red' && right === 'green') || (left === 'green' && right === 'red'));
    assert.equal(JSON.stringify(signature(first)) === JSON.stringify(signature(second)), expected);
    panelCases++;
  }
}

// An independent geometric/arrow oracle, with no compact or scalar value encoder.
function arrowCompatible(placements) {
  const occupied = new Set(), panels = new Map(); let contacts = 0;
  for (const placement of placements) {
    const variant = VARIANTS[placement.variantId];
    for (const cell of variant.cells) {
      const id = key(add(cell, placement.origin));
      if (occupied.has(id)) return { valid: false, contacts };
      occupied.add(id);
    }
    for (const mark of variant.marks) {
      const cell = add(mark.cell, placement.origin);
      const id = key(cell.map((v, i) => 2 * v + 1 + mark.direction[i]));
      const other = panels.get(id);
      if (other) {
        contacts++;
        const colors = [mark.color, other.color].sort().join('/');
        if (key(mark.arrow) !== key(other.arrow) || !mark.direction.every((v, i) => v === -other.direction[i]) || !['blue/blue', 'green/red'].includes(colors)) return { valid: false, contacts };
      }
      panels.set(id, mark);
    }
  }
  return { valid: true, contacts };
}
let pairs = 0, neighbors = 0;
for (const variant of VARIANTS) for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) for (let z = -2; z <= 2; z++) {
  const pair = [{ variantId: 0, origin: [0, 0, 0] }, { variantId: variant.id, origin: [x, y, z] }];
  const expected = arrowCompatible(pair);
  assert.equal(verifyLatticePatch(pair).valid, expected.valid, `${variant.id}@${x},${y},${z}`);
  if (expected.valid && expected.contacts) neighbors++;
  pairs++;
}
assert.equal(neighbors, 44);
for (let level = 0; level <= 3; level++) {
  const result = verifyLatticePatch(chairLeaves(level));
  assert.ok(result.valid);
  assert.equal(result.occupiedPoints, 7 * 8 ** level);
}
console.log(`Scalar lattice marking passed: ${panelCases} panel cases, ${pairs} tile pairs, 44 neighbors, pure-pullback rotations, and four patch sizes.`);
