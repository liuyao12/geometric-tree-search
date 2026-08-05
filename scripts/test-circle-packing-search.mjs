import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { CirclePackingSearch } from "../assets/circle-packing-search.js";

assert.throws(() => new CirclePackingSearch([1, 3]), /at least 2/);

const thirds = new CirclePackingSearch([3], { maxCircles: 7, nodeLimit: 20000 });
while (thirds.status === "running") thirds.step(100);
assert.equal(thirds.status, "found");
assert.equal(thirds.solution.circles.length, 4);
assert.ok(thirds.solution.contacts.every(neighbors => neighbors.size >= 3));

const seed = [{ denominator: 3, radius: 1 / 3, x: 2 / 3, y: 0 }];
const upper = thirds.placeAtCorner(seed, -1, 0, 3).circle;
const lower = thirds.placeAtCorner(seed, 0, -1, 3).circle;
assert.ok(upper && lower);
assert.ok(upper.y > 0);
assert.ok(Math.abs(upper.x - lower.x) < 1e-12);
assert.ok(Math.abs(upper.y + lower.y) < 1e-12);

const html = readFileSync(new URL("../apps/circle-packing-search/index.html", import.meta.url), "utf8");
for (const id of ["denominators", "max-circles", "node-limit", "run", "step", "reset", "packing"]) {
  assert.match(html, new RegExp(`id=["']${id}["']`));
}

console.log(`circle-packing-search: ${thirds.nodes} nodes, ${thirds.solution.circles.length}-circle witness`);
