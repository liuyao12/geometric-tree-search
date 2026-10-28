import assert from 'node:assert/strict';
import { makeIcosahedralPatch } from '../assets/icosahedral-exact.js';
import { makeDisplayModel } from '../apps/quasicrystal-exact/display-model.js';

const patch = makeIcosahedralPatch({ radius: 1 });
const serialize = x => JSON.stringify(x, (_, v) => typeof v === 'bigint' ? String(v) : v);
const before = serialize(patch), model = makeDisplayModel(patch);
assert.equal(model.tiles.length, 540);
assert.equal(model.connected.length, 340);
assert.equal(new Set(model.connected).size, 340);
assert.equal(model.window.vertices.length, 32);
assert.equal(model.window.faces.length, 30);
const edges = new Map();
const center = model.window.vertices.reduce((s, p) => s.map((x, i) => x + p[i] / 32), [0, 0, 0]);
for (const f of model.window.faces) {
  for (let i = 0; i < 4; i++) {
    const key = [f[i], f[(i + 1) % 4]].sort((a, b) => a - b).join(',');
    edges.set(key, (edges.get(key) ?? 0) + 1);
  }
  const [a, b, , d] = f.map(i => model.window.vertices[i]);
  const u = b.map((x, i) => x - a[i]), v = d.map((x, i) => x - a[i]);
  const n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
  assert(n.reduce((s, x, i) => s + x * (center[i] - a[i]), 0) < 0, 'Outward window faces');
}
assert.equal(edges.size, 60);
assert([...edges.values()].every(n => n === 2));
assert.equal(model.window.points.length, 1446);
assert(model.tiles.every(t => t.vertices.flat().every(Number.isFinite)));
assert.deepEqual(model.tiles[0].exact, patch.tiles[0].vertices.map(p => p.map(x => x.toJSON())));
assert.equal(serialize(patch), before, 'Rendering adapter must leave the exact source and export unchanged');
console.log('ok: 540 display tiles; 340 connected tiles; exact source unchanged; outward closed window with 32 vertices, 60 edges, 30 faces; 1446 accepted points');
