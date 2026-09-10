import assert from 'node:assert/strict';
import {Worker} from 'node:worker_threads';
import {periodicStream} from '../apps/3d-lattice-tiler/periodic-search.js';
const moduleURL=new URL('../apps/3d-lattice-tiler/growth-benchmark-worker.js',import.meta.url).href;
const source=`import {parentPort} from 'node:worker_threads';globalThis.self={postMessage:data=>parentPort.postMessage(data)};await import(${JSON.stringify(moduleURL)});parentPort.on('message',data=>self.onmessage({data}));`;
async function run(mode,config,pauseTwice=false) {
  const worker=new Worker(new URL(`data:text/javascript,${encodeURIComponent(source)}`)),messages=[];
  try {
    await new Promise((resolve,reject)=> {
      const timer=setTimeout(()=>reject(Error('worker timeout')),30000);let pauses=0;
      worker.on('error',reject);
      worker.on('message',m=> {
        messages.push(m);
        if(m.type==='error'){clearTimeout(timer);reject(Error(m.error));}
        if(m.type==='mode-ready')worker.postMessage({type:'go',sequence:1,startEpochMs:performance.timeOrigin+performance.now()});
        if(m.type==='mode-paused'&&pauseTwice) {
          if(++pauses===2){clearTimeout(timer);resolve();}
          else worker.postMessage({type:'extend-time',sequence:1,additionalTimeMs:500});
        }
        if(m.type==='finished'){clearTimeout(timer);resolve();}
      });
      worker.postMessage({type:'prepare',sequence:1,mode,config:{mode_key:'mathematica_16_vertex',criterion:'count',target_val:24,include_mirrors:false,periodic_patch_max_tiles:8,...config}});
    });
    return messages;
  }finally{await worker.terminate();}
}
for(const mode of ['translational','isohedral']) {
  const bounded=await run(mode,{periodic_hnf_candidate_limit:1});
  const samples=bounded.flatMap(m=>m.samples??[]),final=bounded.find(m=>m.type==='finished').result;
  assert.ok(samples[0].snapshot.faces.length,'seed must be drawable before any quotient succeeds');
  assert.equal(samples[0].snapshot.preview_kind,'seed');
  assert.equal(final.searchIncomplete,true);assert.equal(final.certified,false);assert.equal(final.tileCount,1);
  assert.equal(final.terminationReason,'quotient_limit');assert.equal(final.searchScope.max_tiles,8);
  assert.ok(bounded.some(m=>m.type==='mode-status'&&m.text.includes('cells')));
  const success=await run(mode,{mode_key:'cube',target_val:1});
  const snapshots=success.flatMap(m=>m.samples??[]).filter(s=>s.snapshot).map(s=>s.snapshot);
  assert.equal(snapshots[0].tile_count,1);assert.equal(snapshots.at(-1).tile_count,1);
  assert.equal(snapshots.at(-1).preview_kind,null,'same-count certified snapshot must replace seed');
  assert.equal(success.find(m=>m.type==='finished').result.certified,true);
  const paused=await run(mode,{time_limit_ms:500},true);
  assert.equal(paused.filter(m=>m.type==='mode-paused').length,2);
  const history=paused.flatMap(m=>m.samples??[]);
  assert.ok(history.length>2,'progress must extend the curve while still searching');
  assert.ok(history.at(-1).point.milliseconds>history[0].point.milliseconds);
  assert.ok(history.some(s=>s.stats?.quotients>0));
  assert.ok(!paused.some(m=>m.type==='finished'));
}
// Unsupported exact input still has a preview and an explicit reason.
const raw={verts:[[0,0,0]],faces:[[0]],occupancy:[{pos:[0,0,0],weight:0.5}]};
const messages=[];
for await(const m of periodicStream({},[{unique_orientations:[raw]}],1,['red']))messages.push(m);
assert.ok(messages.find(m=>m.type==='full_update').faces.length);
assert.equal(messages.at(-1).termination_reason,'unsupported_exact_data');
assert.equal(messages.at(-1).can_tile,null);
console.log('Periodic worker: live seed, inconclusive history/status, same-count certificate replacement, progress, pause/resume, unsupported preview passed in both lanes.');
