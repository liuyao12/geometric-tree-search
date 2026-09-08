import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createMixedGrowth } from "../assets/penrose-mixed-growth.js";
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
for (const [id, value] of Object.entries({ pointDensity: "contacts", extent: "2", markingDirections: "5", stripeWidth: "1.5" })) elements.get(id).value = value;
for (const kind of ["thick", "thin"]) elements.get("tile_" + kind).checked = true;
globalThis.document = { getElementById(id) { assert(elements.has(id), `missing control ${id}`); return elements.get(id); } };
globalThis.window = { addEventListener() {} };
globalThis.devicePixelRatio = 1;
globalThis.requestAnimationFrame = () => {};
const workers = [];
globalThis.Worker = class {
  constructor() { this.messages = []; this.terminated = false; workers.push(this); }
  terminate() { this.terminated = true; }
  postMessage(message) {
    if (message.type === "inspect") { queueMicrotask(() => this.onmessage?.({data:{type:"inspection",key:message.key,contacts:{points:[],candidates:[]}}})); return; }
    this.messages.push(message);
    if (message.type === "init") { this.growth = (message.options.tileKinds.length === 2 && message.options.tileKinds.includes("thick") && message.options.tileKinds.includes("thin") ? createPenroseGrowth : createMixedGrowth)(message.options); this.growth.next(); }
    else this.growth.next();
    queueMicrotask(() => this.onmessage?.({ data: { ...this.growth.snapshot(), done: false, computeMs: 0 } }));
  }
};
await import("../apps/penrose-model-set/demo.js");
const flush = () => new Promise(resolve => setImmediate(resolve));
await flush();
assert.equal(workers.length, 1); assert.equal(workers[0].messages[0].options.useMarkings, false);
assert.equal(workers[0].messages[0].options.targetCount, null);
assert.equal(elements.get("startTiling").textContent, "Run");
elements.get("tilingCanvas").fire("pointermove", { clientX: 400, clientY: 250 });
assert.equal(elements.get("pointTooltip").hidden, false);
assert.equal(elements.get("point_coordinate").textContent, "x = 0");
assert.match(elements.get("point_t").textContent, /t\(x\) = [1-4]\/5/);
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
elements.get("pointDensity").value = "integers"; elements.get("pointDensity").fire("change");
assert.equal(workers.length, 1); assert.equal(workers[0].messages.length, 1, "display controls and contact filter must not touch the search");
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
assert.equal(elements.get("startTiling").textContent, "Continue");
assert.equal(elements.get("statusMessage").textContent, "pausing at corona 3");
elements.get("stepTiling").fire("click"); await flush();
assert.equal(workers[2].messages.at(-1).targetCorona, 5);
assert.equal(workers.length, 3, "continuation preserves the worker");
assert.equal(elements.has("playbackSpeed"), false);
assert.equal(elements.has("coronaCount"), false);
assert.equal(elements.has("runState"), false);
assert.equal(elements.has("shuffleSeed"), false);
assert.equal(elements.has("nodeLimit"), false);
assert.equal(workers[0].messages[0].options.seed, 17);
assert.equal(workers[0].messages[0].options.nodeLimit, 100000);
console.log("ok: one canvas/worker; checkbox switches predicates; highlighting preserves all five enforced directions; display-only controls preserve search; corona continuation and fixed internal settings");

elements.get("tileSet").value = "P2"; elements.get("tileSet").fire("change"); await flush();
assert.deepEqual(workers.at(-1).messages[0].options.tileKinds, ["kite", "dart"]);
assert.equal(workers.at(-1).growth.snapshot().tiles[0].kind, "kite");
assert.equal(elements.get("showMarking").textContent, "Show edge decorations");
elements.get("tile_p5").checked = true; elements.get("tile_p5").fire("change"); await flush();
assert.deepEqual(workers.at(-1).messages[0].options.tileKinds, ["kite", "dart", "p5"]);
assert.match(elements.get("tileHint").textContent, /P1 edges cannot join/);
for (const id of ids.filter(id => id.startsWith("tile_"))) elements.get(id).checked = false;
elements.get("tile_p5").fire("change"); await flush();
assert.equal(elements.get("statusMessage").textContent, "Choose at least one tile");
elements.get("tileSet").value = "P1"; elements.get("tileSet").fire("change"); await flush();
assert.equal(workers.at(-1).growth.snapshot().tiles[0].kind, "p5");
console.log("ok: presets, custom selection, mixed rendering, empty selection and recovery");
const last = workers.at(-1);
const updateActivity = (activity, pausedCorona = null) => last.onmessage({ data: { ...last.growth.snapshot(), activity, pausedCorona, done: false, computeMs: 0 } });
updateActivity({kind:'branch',count:3,frontier:'1,0,1,0/1'});
elements.get('startTiling').fire('click');
assert.equal(elements.get('statusMessage').textContent,'3-way branching at [1 + ζ₅²]');
updateActivity({kind:'forced',count:7});
assert.equal(elements.get('statusMessage').textContent,'7 forced moves');
updateActivity({kind:'forced',count:8},3);
assert.equal(elements.get('statusMessage').textContent,'8 forced moves · pausing at corona 3');
console.log('ok: visible branch coordinates, forced streak and corona pause status');
