import assert from 'node:assert/strict';
import { BASE_MARKS, VARIANTS, FACE_DIRECTIONS, apply, key } from '../3d-reptiles/chair/chair44.js';
import { reliefFeatures, reliefFrame, reliefPoint, reliefHeight } from '../3d-reptiles/chair/relief-profile.js';

const pointKey = p => p.map(v => Math.round(v * 1e9)).join(',');
function surfaces(mark) {
  const frame = reliefFrame(mark);
  return reliefFeatures(mark.color).map(feature => [
    reliefPoint(frame, feature.u, feature.v, feature.height),
    ...[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([u, v]) =>
      reliefPoint(frame, feature.u + feature.radius * u, feature.v + feature.radius * v)),
  ]);
}
const signature = features => features.map(([apex, ...base]) => pointKey(apex) + ':' + base.map(pointKey).sort().join(';')).sort().join('|');
let cases = 0;
for (const normal of FACE_DIRECTIONS) {
  const axis = normal.findIndex(v => v !== 0);
  const arrows = [-1, 1].flatMap(a => [-1, 1].map(b => {
    const values = [a, b]; return normal.map((_, i) => i === axis ? 0 : values.shift());
  }));
  for (const a of arrows) for (const b of arrows) for (const left of ['red', 'green', 'blue']) for (const right of ['red', 'green', 'blue']) {
    const first = { cell: [0, 0, 0], direction: normal, arrow: a, color: left };
    const second = { cell: normal, direction: normal.map(v => -v), arrow: b, color: right };
    const compatible = key(a) === key(b) && ((left === 'blue' && right === 'blue') || (left === 'red' && right === 'green') || (left === 'green' && right === 'red'));
    // Comparing the actual four-sided pyramid bases and tips proves the two
    // piecewise planar interfaces coincide, beyond checking sampled heights.
    assert.equal(signature(surfaces(first)) === signature(surfaces(second)), compatible);
    if (compatible) for (let x = -5; x <= 5; x++) for (let y = -5; y <= 5; y++) {
      const point = reliefPoint(reliefFrame(first), x / 10, y / 10);
      assert.ok(Math.abs(reliefHeight(first, point) + reliefHeight(second, point)) < 1e-12);
    }
    cases++;
  }
}
for (const variant of VARIANTS) for (let i = 0; i < BASE_MARKS.length; i++) {
  const transformed = surfaces(BASE_MARKS[i]).map(feature => feature.map(point =>
    apply(variant.rotation, point.map(v => v - 1)).map(v => v + 1)));
  assert.equal(signature(transformed), signature(surfaces(variant.marks[i])));
}
// The blue pair touches along a whole base edge, with no gap or crease.
const [raised, recessed] = reliefFeatures('blue');
assert.equal(raised.u - raised.radius, recessed.u + recessed.radius);
assert.equal(raised.v, recessed.v);
assert.equal(raised.radius, recessed.radius);
const blue = { cell: [0, 0, 0], direction: [0, 0, 1], arrow: [1, 1, 0], color: 'blue' };
const blueFrame = reliefFrame(blue);
for (let step = -16; step <= 16; step++) {
  const u = step / 100;
  const height = reliefHeight(blue, reliefPoint(blueFrame, u, raised.v));
  assert.ok(Math.abs(height - raised.height * u / raised.u) < 1e-12,
    'The entire apex-to-apex slope is one continuous plane');
}
let protrusions = 0, indents = 0, volumeDelta = 0;
for (const mark of BASE_MARKS) for (const feature of reliefFeatures(mark.color)) {
  if (feature.height > 0) protrusions++; else indents++;
  volumeDelta += 4 * feature.radius ** 2 * feature.height / 3;
  for (const point of surfaces(mark).flatMap(feature => feature.slice(1))) {
    point.forEach((v, i) => {
      if (mark.direction[i] === 0) assert.ok(v > mark.cell[i] && v < mark.cell[i] + 1, 'Relief footprints stay away from panel edges');
    });
  }
}
assert.equal(protrusions, 16);
assert.equal(indents, 16);
assert.ok(Math.abs(volumeDelta) < 1e-12);
console.log(`Relief passed: ${cases} exact facing-surface comparisons, all 24 rotations, 16 bumps/16 recesses, and unchanged volume.`);
