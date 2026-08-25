#!/usr/bin/env node

import assert from "node:assert/strict";
import { GeometricFrontierMarking } from "../assets/geometric-frontier-marking.js";
import { GeometricFailureMemo } from "../assets/geometric-failure-memo.js";
import { PROPER_CUBIC_ROTATIONS } from "../apps/3d-lattice-tiler/engine.js";

const orientation = vertices => ({ verts: vertices });
const shape = orientation([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]);
const placement = (translation, prototile_idx = 0) => ({ prototile_idx, orient: shape, translation });
const rotate = (matrix, vector) => [
  matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
  matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
  matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
];
const rotatedPlacement = (item, matrix, shift) => ({
  ...item,
  orient: orientation(item.orient.verts.map(vertex => rotate(matrix, vertex))),
  translation: rotate(matrix, item.translation).map((value, axis) => value + shift[axis])
});

const point = [1, 1, 1];
const context = [placement([0, 0, 0]), placement([1, 1, 0])];
const marking = new GeometricFrontierMarking({ rotations: PROPER_CUBIC_ROTATIONS, reach: 2 });
assert.equal(marking.compatible(point, 0.5, context), true, "cold marking accepts every state");
assert.equal(marking.encode(point, 0.5, context).encoded, true);
assert.ok(marking.stats().context_tokens > 0, "marking memory reports retained geometry tokens");
assert.ok(marking.stats().payload_bytes > 0, "marking memory reports a deterministic payload lower bound");
assert.equal(marking.compatible(point, 0.5, context), false, "the learned obstruction rejects an exact recurrence");

const shift = [7, -4, 3];
const translated = context.map(item => ({
  ...item,
  translation: item.translation.map((value, axis) => value + shift[axis])
}));
assert.equal(
  marking.compatible(point.map((value, axis) => value + shift[axis]), 0.5, translated),
  false,
  "absolute position is not pre-existing knowledge"
);

const quarterTurn = PROPER_CUBIC_ROTATIONS.find(matrix =>
  rotate(matrix, [1, 0, 0]).join(",") === "0,1,0"
  && rotate(matrix, [0, 1, 0]).join(",") === "-1,0,0"
);
assert.ok(quarterTurn);
const rotated = context.map(item => rotatedPlacement(item, quarterTurn, shift));
const rotatedPoint = rotate(quarterTurn, point).map((value, axis) => value + shift[axis]);
assert.equal(marking.compatible(rotatedPoint, 0.5, rotated), false, "proper lattice rotations act equivariantly");
assert.equal(marking.compatible(rotatedPoint, 0.25, rotated), true, "the frontier marking value is part of the obstruction");

const remoteExtra = placement([100, 100, 100], 1);
assert.equal(
  marking.compatible(rotatedPoint, 0.5, [...rotated, remoteExtra]),
  false,
  "irrelevant placements do not hide a local obstruction"
);

const bounded = new GeometricFrontierMarking({ rotations: PROPER_CUBIC_ROTATIONS, reach: 2, maxContext: 1 });
assert.equal(bounded.encode(point, 0.5, context).encoded, false, "oversize contexts are skipped, never unsafely truncated");
assert.equal(bounded.stats().clauses, 0);

const failureMemo = new GeometricFailureMemo({
  describePlacement: item => ({
    kind: String(item.prototile_idx),
    orientation: "tetrahedron",
    translation: item.translation
  }),
  contextMatch: "subset"
});
assert.equal(failureMemo.encode([context[0]], context[1]).encoded, true);
assert.equal(failureMemo.compatible(context[1], [context[0]]), false);
assert.equal(
  failureMemo.compatible(
    { ...context[1], translation: [8, -3, 3] },
    [{ ...context[0], translation: [7, -4, 3] }, remoteExtra]
  ),
  false,
  "complete failed contexts recur under translation and harmless supersets"
);
assert.ok(failureMemo.stats().context_tokens > 0);
assert.ok(failureMemo.stats().payload_bytes > 0);

console.log("geometric frontier marking tests passed");
