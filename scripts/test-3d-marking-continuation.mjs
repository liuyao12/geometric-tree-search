import assert from 'node:assert/strict';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {learnMarking} from '../apps/3d-lattice-tiler/marking-learning.js';
import {markingSystem} from '../apps/3d-lattice-tiler/marking-storage.js';
import {preprocessTilingSystem,legacyMarkingModel,createTilingStream,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
const collect=async stream=>{const events=[];for await(const e of stream)events.push(e);return events;};
const checkpoint=(model,marking)=>({domain:markingSystem(model),marking});
const model=prepareModel({tile:'cube',radius:1,mirrors:false});
const low=(await collect(learnMarking(model,{timeMs:10000,pairNodes:1}))).at(-1).marking;
assert.ok(!low.accepted);assert.ok(low.counts.unresolved);assert.equal(low.totalPairs,26);
const copy=structuredClone(low),entry=checkpoint(model,low);
const events=await collect(learnMarking(model,{timeMs:10000,pairNodes:500,checkpoint:entry})),final=events.at(-1).marking;
assert.ok(final.accepted);assert.equal(final.pairs,26);assert.deepEqual(low,copy,'Continuation must not mutate its checkpoint');
assert.equal(events.filter(e=>e.phase==='pair').length,low.counts.unresolved);
assert.equal(final.retained,low.counts.valid+low.counts.invalid);
assert.equal(final.trainingMs,low.trainingMs+final.elapsedMs);
assert.equal(final.counts.unresolved,0);
assert.ok(events.every(e=>!e.snapshot||e.snapshot.positivePassed===e.snapshot.counts.valid));
const raised=(await collect(learnMarking(model,{timeMs:10000,pairNodes:1,checkpoint:entry}))).at(-1).marking;assert.equal(raised.pairNodes,2);
// A partial catalogue preserves resolved samples and still enumerates unseen pairs.
let stopped=false,partial;
for await(const e of learnMarking(model,{timeMs:10000,stop:()=>stopped})){if(e.phase==='update'&&e.pairs===3)stopped=true;partial=e;}
assert.equal(partial.marking.evidence.length,3);assert.ok(!partial.marking.complete);
const resumed=await collect(learnMarking(model,{timeMs:10000,checkpoint:checkpoint(model,partial.marking)}));assert.ok(resumed.at(-1).marking.accepted);assert.equal(resumed.filter(e=>e.phase==='pair').length,23);
for(const change of [e=>e.domain.capacity++,e=>e.marking.extent++,e=>e.marking.evidence.push(e.marking.evidence[0]),e=>e.marking.evidence[0].placements=[]]){
 const invalid=structuredClone(checkpoint(model,partial.marking));change(invalid);await assert.rejects(collect(learnMarking(model,{checkpoint:invalid})));
}
await assert.rejects(collect(learnMarking(model,{timeMs:0,checkpoint:entry})),/replay budget/);
const run=await collect(runExperiment({tile:'cube',radius:1,mode:'gcts',timeMs:10000,nodes:1000,learningCheckpoint:entry}));assert.equal(run.at(-1).result,'finite_exact');assert.ok(run.at(-1).marking.continued);
const config={mode_key:'cube',tiling_strategy:'learning_free_range',gcts_failure_marking:true,complete_lattice_point_branching:true,criterion:'count',target_val:8,time_limit_ms:10000,node_limit:1000};
const legacyModel=legacyMarkingModel(preprocessTilingSystem(config,tileSpecs));
const legacyLow=(await collect(learnMarking(legacyModel,{timeMs:10000,pairNodes:1}))).at(-1).marking;
const legacy=await collect(createTilingStream({...config,learningCheckpoint:checkpoint(legacyModel,legacyLow)},tileSpecs));assert.ok(legacy.at(-1).success);assert.ok(legacy.find(e=>e.type==='marking-learned').marking.continued);
// Mixed positive/negative evidence is retained without duplicate constraints.
const slab=prepareModel({tile:'a2_turtle_prism',radius:1,mirrors:true});
const slabLow=(await collect(learnMarking(slab,{timeMs:30000,pairNodes:1}))).at(-1).marking;
assert.ok(slabLow.counts.invalid>0&&slabLow.counts.unresolved>0);
const slabEvents=await collect(learnMarking(slab,{timeMs:30000,pairNodes:500,checkpoint:checkpoint(slab,slabLow)}));
const slabFinal=slabEvents.at(-1).marking;
assert.ok(slabFinal.accepted);assert.deepEqual(slabFinal.counts,{valid:41,invalid:206,unresolved:0});assert.ok(slabFinal.negativeBlocked>=192);
const resolved=new Set(slabLow.evidence.filter(r=>r.status!=='unresolved').map(r=>JSON.stringify(r.pair)));
assert.ok(slabEvents.filter(e=>e.phase==='pair').every(e=>!resolved.has(JSON.stringify(e.pair))));
console.log('PASS both engines: retained labels, unresolved retry, larger budget, partial catalogue, identity/witness rejection, cumulative cost and automatic marked tiling.');
