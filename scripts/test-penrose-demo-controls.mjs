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
  fire(type, event = {}) { this.listeners.get(type)?.(event); }
  getBoundingClientRect() { return { left: 0, top: 0 }; }
  setAttribute(key, value) { this.attributes.set(key, value); }
  getContext() { return new Proxy({}, { get: (_, key) => key === "canvas" ? this : () => {} }); }
}
const elements = new Map(ids.map(id => [id, new Element()]));
for (const [id, value] of Object.entries({ pointDensity: "8", extent: "2", markingDirections: "5", stripeWidth: "1.5", nodeLimit: "1000", shuffleSeed: "17", playbackSpeed: "24" })) elements.get(id).value = value;
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
assert.equal(workers[0].messages[0].options.targetCount, null);
assert.equal(elements.get("startTiling").textContent, "Run to corona 3");
elements.get("tilingCanvas").fire("pointermove", { clientX: 400, clientY: 250 });
assert.equal(elements.get("pointTooltip").hidden, false);
assert.equal(elements.get("point_coordinate").textContent, "x = 0");
assert.equal(elements.get("point_t").textContent, "t(x) = 1/5");
assert.match(elements.get("point_m").textContent, /m\(x\) = \(0, 0, 0, 0, 0\)/);
elements.get("tilingCanvas").fire("pointerleave");
assert.equal(elements.get("pointTooltip").hidden, true);
elements.get("showMarking").fire("click"); elements.get("directionColors").fire("input"); elements.get("stripeWidth").fire("input");
const { inspectionPoints } = await import("../apps/penrose-model-set/point-inspection.js");
const endpoint = inspectionPoints(workers[0].growth.snapshot()).find(p => !p.vertex);
elements.get("tilingCanvas").fire("pointermove", { clientX: 400 + endpoint.position.x * 50, clientY: 250 + endpoint.position.y * 50 });
assert.equal(elements.get("pointTooltip").hidden, false);
assert.equal(elements.get("point_title").textContent, "Ammann endpoint");
assert.match(elements.get("point_t").textContent, /t\(x\) = 0/);
assert.match(elements.get("point_m").textContent, /m\(x\) = \(/);
elements.get("pointDensity").value = "16"; elements.get("pointDensity").fire("change");
assert.equal(workers.length, 1); assert.equal(workers[0].messages.length, 1, "display controls and sample density must not touch the search");
elements.get("extent").value = "1.5"; elements.get("extent").fire("input");
assert.equal(workers.length, 1, "extent only changes drawing in arrow mode");
elements.get("useMarkings").checked = true; elements.get("useMarkings").fire("change"); await flush();
assert.equal(workers.length, 2); assert(workers[0].terminated);
assert.equal(workers[1].messages[0].options.useMarkings, true);
assert.equal(elements.get("markingDirections").disabled, false);
elements.get("markingDirections").value = "3"; elements.get("markingDirections").fire("change"); await flush();
assert.equal(workers.length, 2); assert(!workers[1].terminated);
assert.equal(workers[1].messages.length, 1, "highlighting never changes enforcement");
assert.equal(workers[1].growth.snapshot().markingDirections, 5);
assert.equal(workers[1].messages[0].options.seed, workers[0].messages[0].options.seed);
assert.equal(workers[1].messages[0].options.extent, 1.5);
elements.get("extent").value = "2"; elements.get("extent").fire("input"); await flush();
assert.equal(workers.length, 3); assert(workers[1].terminated);
assert.equal(workers[2].messages[0].options.extent, 2, "extent reaches the solver");
elements.get("stepTiling").fire("click"); await flush();
assert.equal(workers[2].messages.at(-1).events, 1);
assert.equal(workers[2].messages.at(-1).targetCorona, 3);
workers[2].onmessage({data:{...workers[2].growth.snapshot(),pausedCorona:3,done:false,computeMs:0}});
assert.equal(elements.get("startTiling").textContent, "Run to corona 5");
elements.get("stepTiling").fire("click"); await flush();
assert.equal(workers[2].messages.at(-1).targetCorona, 5);
assert.equal(workers.length, 3, "continuation preserves the worker");
elements.get("shuffleSeed").value = "1.5"; elements.get("shuffleSeed").fire("change"); await flush();
assert(workers[2].terminated); assert.equal(workers.length, 3);
assert.equal(elements.get("runState").textContent, "error");
console.log("ok: one canvas/worker; checkbox switches predicates; highlighting preserves all five enforced directions; display-only controls preserve search; step and invalid-input handling");
