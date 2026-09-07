import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createPenroseGrowth } from "../assets/penrose-growth.js";

// Controller unit test with a DOM/canvas transport double, not a browser or
// local preview. The real worker protocol has its own integration test.
const html = await readFile(new URL("../apps/penrose-model-set/index.html", import.meta.url), "utf8");
const ids = [...html.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
assert.equal(new Set(ids).size, ids.length);
assert.equal((html.match(/<canvas /g) || []).length, 1);
class Element {
  constructor() { this.checked = false; this.value = ""; this.listeners = new Map(); this.attributes = new Map(); this.clientWidth = 800; this.clientHeight = 500; }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  fire(type) { this.listeners.get(type)?.({}); }
  setAttribute(key, value) { this.attributes.set(key, value); }
  getContext() { return new Proxy({}, { get: (_, key) => key === "canvas" ? this : () => {} }); }
}
const elements = new Map(ids.map(id => [id, new Element()]));
for (const [id, value] of Object.entries({ markingDirections: "5", stripeWidth: "1.5", targetCount: "40", nodeLimit: "1000", shuffleSeed: "17", playbackSpeed: "24" })) elements.get(id).value = value;
globalThis.document = { getElementById(id) { assert(elements.has(id), `missing control ${id}`); return elements.get(id); } };
globalThis.window = { addEventListener() {} };
globalThis.devicePixelRatio = 1;
globalThis.requestAnimationFrame = () => {};
const workers = [];
globalThis.Worker = class {
  constructor() { this.messages = []; this.terminated = false; workers.push(this); }
  terminate() { this.terminated = true; }
  postMessage(message) {
    this.messages.push(message);
    if (message.type === "init") { this.growth = createPenroseGrowth(message.options); this.growth.next(); }
    else this.growth.next();
    queueMicrotask(() => this.onmessage?.({ data: { ...this.growth.snapshot(), done: false, computeMs: 0 } }));
  }
};
await import("../apps/penrose-model-set/demo.js");
const flush = () => new Promise(resolve => setImmediate(resolve));
await flush();
assert.equal(workers.length, 1); assert.equal(workers[0].messages[0].options.useMarkings, false);
elements.get("showMarking").fire("click"); elements.get("directionColors").fire("input"); elements.get("stripeWidth").fire("input");
assert.equal(workers.length, 1); assert.equal(workers[0].messages.length, 1, "display controls must not touch the search");
elements.get("useMarkings").checked = true; elements.get("useMarkings").fire("change"); await flush();
assert.equal(workers.length, 2); assert(workers[0].terminated);
assert.equal(workers[1].messages[0].options.useMarkings, true);
assert.equal(elements.get("markingDirections").disabled, false);
elements.get("markingDirections").value = "3"; elements.get("markingDirections").fire("change"); await flush();
assert.equal(workers.length, 3); assert(workers[1].terminated);
assert.equal(workers[2].messages[0].options.markingDirections, 3);
assert.equal(workers[2].messages[0].options.seed, workers[0].messages[0].options.seed);
elements.get("stepTiling").fire("click"); await flush();
assert.equal(workers[2].messages.at(-1).events, 1);
elements.get("shuffleSeed").value = "1.5"; elements.get("shuffleSeed").fire("change"); await flush();
assert(workers[2].terminated); assert.equal(workers.length, 3);
assert.equal(elements.get("runState").textContent, "error");
console.log("ok: one canvas/worker; checkbox and direction settings restart consistently; display-only controls preserve search; step and invalid-input handling");
