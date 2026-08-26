import assert from "node:assert/strict";
import { policyIdentifiabilityAudit } from "../apps/iqc-growth-live/policy-identifiability.js";

const term = (id, contribution, weight = 1) => ({ id, label: id, contribution, weight,
  role: "test geometry", claimBoundary: "not energy" });
const rows = [0, 1, 2, 3, 4].map((value) => ({ candidateKey: `c${value}`, scoreTerms: [
  term("a", value), term("b", 3 * value + 2), term("c", -value),
  term("d", [0, 4, 1, 3, 2][value]), term("inactive", value, 0),
  term("constant", 7), term("known-window-gain", value), term("exploration", value),
] }));
const audit = policyIdentifiabilityAudit(rows, { candidateSetDigest: "frozen-1" });
assert.equal(audit.candidateCount, 5);
assert.deepEqual(audit.terms.map((entry) => entry.id), ["a", "b", "c", "d"]);
assert.deepEqual(Object.fromEntries(audit.withheld.map((entry) => [entry.id, entry.reason])), {
  inactive: "inactive-zero-weight",
  constant: "constant-on-this-frontier",
  "known-window-gain": "excluded-by-target-blind-contract",
  exploration: "excluded-by-target-blind-contract",
});
const pair = (first, second) => audit.pairs.find((entry) => entry.firstId === first && entry.secondId === second);
assert.equal(pair("a", "b").pearson, 1);
assert.equal(pair("a", "b").spearman, 1);
assert.equal(pair("a", "b").classification, "near-redundant");
assert.equal(pair("a", "c").pearson, -1);
assert.equal(pair("a", "c").spearman, -1);
assert.equal(pair("a", "c").classification, "opposed-rank");
assert.equal(pair("a", "a").classification, "self");
assert.equal(audit.targetUsed, false);
assert.equal(audit.coordinatesEmbedded, false);
assert.equal(audit.candidateSetChanged, false);
assert.match(audit.auditDigest, /^[0-9a-f]{8}$/);

assert.equal(policyIdentifiabilityAudit([rows[0]]), null);
assert.throws(() => policyIdentifiabilityAudit([rows[0], { ...rows[1], candidateKey: "c0" }]), /unique/);

const z = [-2, -1, 0, 0, 1, 2];
const u = [1, -2, 1, -1, 2, -1];
const conditionalRows = z.map((value, index) => ({ candidateKey: `p${index}`, scoreTerms: [
  term("x", 5 * value + u[index]), term("y", 5 * value - u[index]),
] }));
const rawConfounded = policyIdentifiabilityAudit(conditionalRows, { candidateSetDigest: "confounded" });
const conditioned = policyIdentifiabilityAudit(conditionalRows, {
  candidateSetDigest: "confounded", mode: "conditional",
  conditioningVariables: [
    { id: "grammar-priority", label: "grammar", values: z },
    { id: "emitted-site-count", label: "size", values: Array(z.length).fill(4) },
  ],
});
assert.ok(rawConfounded.pairs.find((entry) => entry.firstId === "x" && entry.secondId === "y").pearson > .8);
assert.ok(Math.abs(conditioned.pairs.find((entry) => entry.firstId === "x" && entry.secondId === "y").pearson + 1) < 1e-12);
assert.equal(conditioned.conditioningVariables[0].accepted, true);
assert.equal(conditioned.conditioningVariables[1].accepted, false);
assert.equal(conditioned.conditioningVariables[1].reason, "constant-or-collinear");
assert.notEqual(conditioned.auditDigest, rawConfounded.auditDigest);
assert.match(conditioned.interpretation, /linear projection/);
assert.throws(() => policyIdentifiabilityAudit(conditionalRows, { mode: "invented" }), /Unknown/);
console.log("policy identifiability audit passed");
