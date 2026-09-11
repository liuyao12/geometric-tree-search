// DOM-level control regression; not a screenshot/layout test.
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
class Element {
  constructor() {
    this.children = [];
    this.style = {};
    this.events = {};
    this.textContent = "";
    this.value = "";
  }
  append(...children) {
    this.children.push(...children);
  }
  replaceChildren(...children) {
    this.children = children;
    this.textContent = "";
  }
  setAttribute() {}
  addEventListener(event, fn) {
    this.events[event] = fn;
  }
  text() {
    return [this.textContent, ...this.children.map((c) => c.text())].join(" ");
  }
}
const nodes = Object.fromEntries(
  [
    "print",
    "material",
    "metric",
    "comparison",
    "milestone",
    "atom-count",
    "quality-chart",
    "structure-material", "structure-epsilon", "structure-step", "structure-window", "structure-comparison",
  ].map((id) => [id, new Element()]),
);
nodes.material.value = "ice";
nodes.metric.value = "checks";
nodes.milestone.value = "2";
globalThis.document = {
  getElementById: (id) => nodes[id],
  createElement: () => new Element(),
};
globalThis.window = { print: () => {} };
globalThis.fetch = async (path) => ({
  ok: true,
  json: async () =>
    JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8")),
});
await import("./paper.mjs");
assert.match(nodes.comparison.text(), /7.47×/);
for (const material of ["nacl", "ice", "copper"])
  for (const metric of ["checks", "growth", "total"]) {
    nodes.material.value = material;
    nodes.metric.value = metric;
    nodes.metric.events.change();
    assert.match(nodes.comparison.text(), /All three paired/);
    assert.doesNotMatch(nodes.comparison.text(), /NaN|undefined/);
  }
for (let i = 0; i < 3; i++) {
  nodes.milestone.value = String(i);
  nodes.milestone.events.input();
  assert.equal(nodes["atom-count"].value, `${[64, 128, 220][i]} atoms`);
  assert.match(nodes["quality-chart"].text(), /100%/);
}
assert.match(nodes["quality-chart"].text(), /O 34.*D 186/);
nodes['structure-material'].value='ice'; nodes['structure-epsilon'].value='.03';
nodes['structure-step'].value='220'; nodes['structure-window'].value='6';
await import('./structural-figure.mjs');
assert.match(nodes['structure-comparison'].text(), /114\/128/);
let structuralCases=0;
for(const material of ['ice','copper'])for(const epsilon of (material==='ice'?['.015','.03','.06']:['.03']))
  for(const step of ['64','128','220'])for(const radius of ['2','4','6']){
    nodes['structure-material'].value=material;nodes['structure-epsilon'].value=epsilon;
    nodes['structure-step'].value=step;nodes['structure-window'].value=radius;
    nodes['structure-step'].events.change(); structuralCases++;
    assert.match(nodes['structure-comparison'].text(), /Atom-count ceiling/);
    assert.doesNotMatch(nodes['structure-comparison'].text(), /NaN|undefined/);
  }
assert.equal(structuralCases,36);
const report = JSON.parse(
  readFileSync(new URL("results.json", import.meta.url), "utf8"),
);
assert.equal(report.results.length, 18);
for (const [path, hash] of Object.entries(report.sources))
  assert.equal(
    createHash("sha256")
      .update(readFileSync(new URL("../" + path, import.meta.url)))
      .digest("hex"),
    hash,
    path,
  );
for (const local of report.results.filter((r) => r.mode === "local")) {
  const global = report.results.find(
    (r) => r.mode === "global" && r.id === local.id && r.trial === local.trial,
  );
  for (const key of [
    "traceHash",
    "stateHash",
    "candidateHash",
    "geometryHash",
    "stackHash",
  ])
    assert.equal(local[key], global[key]);
  assert(local.legal && global.legal);
}
const html = readFileSync(new URL("index.html", import.meta.url), "utf8");
assert.match(html, /From Atomic Motifs/);
assert(html.indexOf('id="quality"') < html.indexOf('id="results"'));
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(new Set(ids).size, ids.length, 'Unique page anchors');
for (const [, anchor] of html.matchAll(/href="#([^"]+)"/g))
  assert(ids.includes(anchor), `Missing anchor: ${anchor}`);
for (const [, path] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
  if (/^(https?:|data:|#)/.test(path)) continue;
  assert(existsSync(new URL(path, import.meta.url)), path);
}
console.log(
  "PASS: 9 figure combinations, 3 ice milestones, source hashes, 9 paired equivalence checks, local links.",
);
