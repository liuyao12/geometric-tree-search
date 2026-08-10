import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { CirclePackingSearch } from "../assets/circle-packing-search.js";
import { CIRCLE_PACKING_SAMPLES, hydrateSample } from "../assets/circle-packing-samples.js";

assert.throws(() => new CirclePackingSearch([1, 3]), /at least 2/);

const thirds = new CirclePackingSearch([3], { maxCircles: 7, nodeLimit: 20000 });
while (thirds.status === "running") thirds.step(100);
assert.equal(thirds.status, "found");
assert.equal(thirds.solution.circles.length, 6);
assert.ok(thirds.solution.contacts.every((_, index) => thirds.isHeld(thirds.solution.circles, index, thirds.solution.contacts)));

const seed = [{ bend: 3, radius: 1 / 3, x: 2 / 3, y: 0 }];
const upper = thirds.placeAtCorner(seed, -1, 0, 3).circle;
const lower = thirds.placeAtCorner(seed, 0, -1, 3).circle;
assert.ok(upper && lower);
assert.ok(upper.y > 0);
assert.ok(Math.abs(upper.x - lower.x) < 1e-12);
assert.ok(Math.abs(upper.y + lower.y) < 1e-12);
assert.equal(thirds.stateKey([seed[0], upper]), thirds.stateKey([seed[0], lower]), "reflections share a canonical key");
assert.equal(thirds.actions(seed).length, 1, "the two symmetric second-circle branches collapse to one child");

const rotate = (circle, angle) => ({
  ...circle,
  x: circle.x * Math.cos(angle) - circle.y * Math.sin(angle),
  y: circle.x * Math.sin(angle) + circle.y * Math.cos(angle),
});
const witness = thirds.solution.circles;
assert.equal(thirds.stateKey(witness), thirds.stateKey(witness.map(circle => rotate(circle, .731))), "rotations share a canonical key");
assert.ok(thirds.symmetryPrunes > 0, "the search records symmetry-related children it skipped");

assert.deepEqual(CIRCLE_PACKING_SAMPLES.map(sample => sample.bends), [
  [3], [2, 3], [2, 4], [2, 3, 4], [2, 3, 6], [2, 3, 4, 6], [2, 3, 5, 6],
  [2, 4, 7], [2, 3, 6, 11], [2, 3, 6, 14], [2, 3, 15], [2, 3, 6, 15], [2, 4, 18],
]);
for (const sample of CIRCLE_PACKING_SAMPLES) {
  const verifier = new CirclePackingSearch(sample.bends, { maxCircles: sample.maxCircles });
  const circles = hydrateSample(sample);
  assert.ok(verifier.isVictory(circles), `saved sample ${sample.id} must satisfy the contact goal`);
  for (let i = 0; i < circles.length; i += 1) {
    assert.ok(Math.hypot(circles[i].x, circles[i].y) <= 1 - circles[i].radius + verifier.tolerance);
    for (let j = 0; j < i; j += 1) {
      assert.ok(Math.hypot(circles[i].x - circles[j].x, circles[i].y - circles[j].y)
        >= circles[i].radius + circles[j].radius - verifier.tolerance);
    }
  }
}

const html = readFileSync(new URL("../apps/circle-packing-search/index.html", import.meta.url), "utf8");
for (const id of ["bends", "max-circles", "node-limit", "run", "step", "reset", "packing"]) {
  assert.match(html, new RegExp(`id=["']${id}["']`));
}

console.log(`circle-packing-search: ${thirds.nodes} nodes, ${thirds.solution.circles.length}-circle witness`);
