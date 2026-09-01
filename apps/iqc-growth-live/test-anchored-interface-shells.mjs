import assert from "node:assert/strict";
import { auditAnchoredInterfaceShells } from "./anchored-interface-shells.mjs";

const passed = auditAnchoredInterfaceShells({
  freshIds: ["f0", "f1"],
  shellIds: [["s10", "s11"], ["s20", "s21"]],
  anchorIds: ["a0", "a1"],
  contactPairs: [
    ["f0", "s10"], ["f1", "s11"],
    ["s10", "s20"], ["s11", "s21"],
    ["s20", "a0"], ["s21", "a1"],
  ],
});
assert.equal(passed.passed, true);
assert.deepEqual(passed.shellPopulations, [2, 2]);
assert.equal(passed.allFreshConnectedToFirstShell, true);
assert.equal(passed.allOuterShellConnectedToAnchors, true);
assert.equal(passed.targetUsed, false);

const dangling = auditAnchoredInterfaceShells({
  freshIds: ["f0", "f1"],
  shellIds: [["s10", "s11"], ["s20"]],
  anchorIds: ["a0"],
  contactPairs: [["f0", "s10"], ["f1", "s11"], ["s10", "s20"], ["s20", "a0"]],
});
assert.equal(dangling.passed, false);
assert.deepEqual(dangling.danglingByLayer[1], ["s11"]);

const emptyAnchor = auditAnchoredInterfaceShells({
  freshIds: [1], shellIds: [[2], [3]], anchorIds: [], contactPairs: [[1, 2], [2, 3]],
});
assert.equal(emptyAnchor.passed, false);

assert.throws(() => auditAnchoredInterfaceShells({
  freshIds: [1], shellIds: [[2], [2]], anchorIds: [3], contactPairs: [],
}), /disjoint/);

console.log("anchored interface-shell audit tests passed");
