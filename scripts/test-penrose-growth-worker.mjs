import assert from "node:assert/strict";
import { Worker } from "node:worker_threads";

// Exercise the actual browser-worker module through a small Node transport
// adapter. No local web server or browser preview is required.
const moduleURL = new URL("../apps/penrose-model-set/growth-worker.js", import.meta.url).href;
const source = `import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:data=>parentPort.postMessage(data)};
await import(${JSON.stringify(moduleURL)});
parentPort.on('message',data=>self.onmessage({data}));`;
const worker = new Worker(new URL(`data:text/javascript,${encodeURIComponent(source)}`));
const request = message => new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("worker timed out")), 10000);
  worker.once("message", data => { clearTimeout(timer); resolve(data); });
  worker.postMessage(message);
});
try {
  let state = await request({ type: "init", options: { useMarkings: true, extent: 2, targetCount: 40, nodeLimit: 100, seed: 17 } });
  assert.equal(state.extent, 2); assert.equal(state.tiles.length, 1); assert.equal(state.done, false);
  let batches = 0;
  while (!state.done) {
    state = await request({ type: "advance", events: 50 }); assert(!state.error); batches++;
    assert(state.stats.proposals <= 100);
  }
  assert(batches > 1); assert.equal(state.status, "budget reached");
  const frozen = await request({ type: "advance", events: 50 }); assert.deepEqual(frozen, state);
  const invalid = await request({ type: "init", options: { targetCount: -1 } }); assert(invalid.error);
  console.log("ok: actual worker initialization, bounded live batches, terminal freeze, and invalid-input reporting");
} finally { await worker.terminate(); }
