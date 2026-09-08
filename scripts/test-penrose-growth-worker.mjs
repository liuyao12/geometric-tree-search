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
  let state = await request({ type: "init", options: { useMarkings: true, extent: 2, targetCount: 40, nodeLimit: 2, seed: 17 } });
  assert.equal(state.extent, 2); assert.equal(state.tiles.length, 1); assert.equal(state.done, false);
  let batches = 0;
  while (!state.done) {
    state = await request({ type: "advance", events: 50 }); assert(!state.error); batches++;
    assert(state.stats.proposals <= 2);
  }
  assert(batches >= 1); assert.equal(state.status, "budget reached");
  const frozen = await request({ type: "advance", events: 50 }); assert.deepEqual(frozen, state);
  state = await request({type:"init",options:{useMarkings:true,extent:2,targetCount:null,nodeLimit:10000,seed:17}});
  let previousProposals = 0;
  for (const targetCorona of [3,5]) {
    do {
      state = await request({type:"advance",events:200,targetCorona});
      assert(!state.error); assert(!state.done, "milestones suspend, not terminate");
    } while (state.pausedCorona !== targetCorona);
    assert.equal(state.minimumFrontierGeneration,targetCorona);
    assert.equal(state.graph.fullBuilds,1); assert.equal(state.graph.deadPoints,0);
    assert(state.stats.proposals > previousProposals); previousProposals=state.stats.proposals;
    const totals=new Map(), depths=new Map();
    for (const tile of state.tiles) tile.vertices.forEach((v,k)=>{
      totals.set(v,(totals.get(v)||0)+tile.weights[k]);
      depths.set(v,Math.min(depths.get(v)??Infinity,tile.generation));
    });
    assert.equal(Math.min(...[...totals].filter(([,t])=>t>0&&t<10).map(([v])=>depths.get(v))),targetCorona);
  }
  assert(state.tiles.length>40,"corona target is independent of old tile count");
  state = await request({type:"init",options:{tileKinds:["kite","dart"],useMarkings:true,extent:2,targetCount:null,nodeLimit:10000,seed:17}});
  assert.equal(state.mixed,true);
  for (const targetCorona of [3,5]) {
    do { state = await request({type:"advance",events:200,targetCorona}); assert(!state.error); assert(!state.done); } while(state.pausedCorona!==targetCorona);
    assert.equal(state.minimumFrontierGeneration,targetCorona);
    assert.equal(state.graph.fullBuilds,1); assert.equal(state.graph.deadPoints,0);
    assert(state.tiles.every(t=>["kite","dart"].includes(t.kind)));
  }
  const invalid = await request({ type: "init", options: { targetCount: -1 } }); assert(invalid.error);
  console.log("ok: actual worker initialization, bounded live batches, terminal freeze, and invalid-input reporting");
} finally { await worker.terminate(); }
