import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const extract = (name, nextName) => {
  const match = source.match(new RegExp(`function ${name}\\([\\s\\S]*?\\n}\\n\\nfunction ${nextName}`));
  assert.ok(match, `${name} must remain extractable`);
  return Function(`"use strict"; return (${match[0].replace(new RegExp(`\\n\\nfunction ${nextName}$`), "")});`)();
};
const notebookStringHash = extract("notebookStringHash", "notebookControlledResponseSweeps");
const controlledSource = source.match(/function notebookControlledResponseSweeps\([\s\S]*?\n}\n\nfunction compactNotebookSweepSetting/);
assert.ok(controlledSource);
const notebookControlledResponseSweeps = Function("notebookStringHash",
  `"use strict"; return (${controlledSource[0].replace(/\n\nfunction compactNotebookSweepSetting$/, "")});`)(notebookStringHash);

const factors = ({ marking, boundary = "box", structuralObservable = "rdf" }) => ({
  pipeline: { label: "pipeline extent", role: "execution", value: "material growth:4" },
  boundary: { label: "external boundary", role: "geometry", value: boundary },
  clustering: { label: "cluster geometry", role: "geometry", value: "off-lattice:0.07" },
  marking: { label: "GCTS marking", role: "learned representation", value: marking },
  structuralObservable: { label: "posthoc structural observable", role: "analysis only", value: structuralObservable },
  costModel: { label: "cost estimate assumptions", role: "analysis only", value: "linear" },
});
const entry = (id, marking, overrides = {}) => ({
  id,
  material: "NaCl",
  inputIdentity: overrides.inputIdentity || "nacl:sha-input",
  inputStructureSha256: overrides.inputStructureSha256 || "0123456789abcdef",
  interventionFactors: factors({ marking, boundary: overrides.boundary, structuralObservable: overrides.observable }),
  receiptSha256: `receipt-${id}`,
});

const clean = notebookControlledResponseSweeps([
  entry("a", "mark-a"), entry("b", "mark-b"), entry("c", "mark-c"), entry("d", "mark-c", { observable: "sq" }),
]);
assert.equal(clean.length, 1);
assert.equal(clean[0].factorKey, "marking");
assert.equal(clean[0].settings.length, 3);
assert.equal(clean[0].entries.length, 4);
assert.equal(clean[0].settings.find((setting) => setting.value === "mark-c").entries.length, 2);
assert.equal(clean[0].controlled, true);
assert.equal(clean[0].coordinatesEmbedded, false);
assert.equal(clean[0].physicalTimeModeled, false);
assert.equal(clean[0].inputStructureSha256, "0123456789abcdef");

assert.deepEqual(notebookControlledResponseSweeps([entry("a", "mark-a"), entry("b", "mark-b")]), []);
assert.deepEqual(notebookControlledResponseSweeps([
  entry("a", "mark-a", { inputIdentity: "input-a" }),
  entry("b", "mark-b", { inputIdentity: "input-b" }),
  entry("c", "mark-c", { inputIdentity: "input-c" }),
]), []);
assert.deepEqual(notebookControlledResponseSweeps([
  entry("a", "mark-a", { boundary: "box" }),
  entry("b", "mark-b", { boundary: "sphere" }),
  entry("c", "mark-c", { boundary: "slab" }),
]), []);
assert.deepEqual(notebookControlledResponseSweeps([
  entry("a", "same", { observable: "rdf" }),
  entry("b", "same", { observable: "sq" }),
  entry("c", "same", { observable: "order" }),
]), [], "analysis-only observable changes must not manufacture an intervention sweep");

assert.equal(notebookStringHash("same"), notebookStringHash("same"));
assert.notEqual(notebookStringHash("mark-a"), notebookStringHash("mark-b"));
console.log("notebook controlled response sweep: passed");
