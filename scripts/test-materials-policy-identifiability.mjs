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
console.log("policy identifiability audit passed");
