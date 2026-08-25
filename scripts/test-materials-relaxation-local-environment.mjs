import assert from "node:assert/strict";
import { bestAffineNeighborhoodResidual } from "../apps/iqc-growth-live/relaxation-local-environment.js";

const source = [
  [1, 0, 0], [0, 1, 0], [0, 0, 1],
  [-1, 0, 0], [0, -1, 0], [0, 0, -1],
  [1, 1, 0], [0, 1, 1], [1, 0, 1],
];
const affine = [
  [0, -1.1, 0.2],
  [1.2, 0.1, 0],
  [0.05, 0.15, 0.9],
];
const transform = (vector) => affine.map((row) => row.reduce(
  (sum, value, axis) => sum + value * vector[axis], 0));
const exact = bestAffineNeighborhoodResidual(source, source.map(transform));
assert.ok(exact.rootD2Min < 1e-8, `exact affine residual ${exact.rootD2Min}`);

const disturbed = source.map(transform);
disturbed[0] = [disturbed[0][0] + 0.35, disturbed[0][1] - 0.2, disturbed[0][2] + 0.1];
const rearranged = bestAffineNeighborhoodResidual(source, disturbed);
assert.ok(rearranged.rootD2Min > 0.05);

const planarSource = [[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0], [1, 1, 0], [-1, 1, 0]];
const planarTarget = planarSource.map(([x, y]) => [1.1 * x + 0.2 * y, -0.15 * x + 0.9 * y, 0]);
const planar = bestAffineNeighborhoodResidual(planarSource, planarTarget);
assert.ok(planar.rootD2Min < 1e-8, `regularized planar residual ${planar.rootD2Min}`);

assert.throws(() => bestAffineNeighborhoodResidual([[1, 0, 0]], [[1, 0, 0]]), /at least three/);
console.log("materials relaxation local environment: affine, non-affine, and planar checks passed");
