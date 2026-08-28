import assert from "node:assert/strict";
import { geometricConstraintTensor } from "../apps/iqc-growth-live/geometric-constraint-tensor.mjs";

const axes = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const rigid = geometricConstraintTensor(axes, "rigid-3d");
rigid.eigenvalues.forEach((value) => assert.ok(Math.abs(value - 1 / 3) < 1e-11));
assert.equal(rigid.rank, 3);
assert.ok(rigid.score > .999999);
assert.ok(rigid.effectiveDimension > 2.999999);

const plane = geometricConstraintTensor([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]], "lamellar");
assert.deepEqual(plane.eigenvalues, [.5, .5, 0]);
assert.equal(plane.rank, 2);
assert.ok(plane.score > .999999);

const line = geometricConstraintTensor([[3, 0, 0], [-7, 0, 0]], "axial");
assert.deepEqual(line.eigenvalues, [1, 0, 0]);
assert.equal(line.rank, 1);
assert.ok(line.score > .999999);

const angle = .713;
const rotate = ([x, y, z]) => [Math.cos(angle) * x - Math.sin(angle) * y,
  Math.sin(angle) * x + Math.cos(angle) * y, z];
const transformed = geometricConstraintTensor(axes.map((vector) => rotate(vector).map((value) => 4.2 * value)).reverse(), "rigid-3d");
assert.deepEqual(transformed.eigenvalues, rigid.eigenvalues);
assert.equal(transformed.score, rigid.score);
assert.equal(transformed.targetUsed, false);
assert.equal(transformed.forceConstantsUsed, false);
assert.equal(geometricConstraintTensor([], "rigid-3d").score, -1);
console.log("geometric constraint tensor contract passed");
