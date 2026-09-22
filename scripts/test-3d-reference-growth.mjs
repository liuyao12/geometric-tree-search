import assert from 'node:assert/strict';
import {solveA2Tiling,NoA2Marking,tileOrientations,A2_TILE_LOOPS} from '../assets/a2-tiling-engine.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {GrowthGraph,grow,verifyGrowth,orderGrowthCandidates} from '../apps/3d-lattice-tiler/growth-search.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {allowedTranslation,pointKey,add,sub,placementKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {markingSlots} from '../apps/3d-lattice-tiler/v2/search.js';
import {createTilingStream,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
const seed={oi:0,translation:[0,0,0]};
const digest=g=>JSON.stringify({totals:[...g.totals].sort(),section:[...g.section].sort(),generation:[...g.generations].map(([k,v])=>[k,[...v].sort()]).sort(),active:[...g.active].sort(),selected:g.descriptors(),degrees:[...g.points].map(([k,p])=>[k,p.degree]).sort()});
// Independent brute-force candidate enumeration, including candidates absent
// from caches, checks every active point and all marking-only dependencies.
function audit(g){
 g.audit();const m=g.model;
 for(const k of g.active){
  const expected=new Set(),pos=k.split(',').map(Number);
  for(let oi=0;oi<m.orientations.length;oi++)for(const anchor of m.orientations[oi].cells){
   const translation=sub(pos,anchor.pos),id=placementKey({oi,translation});if(!allowedTranslation(m,translation)||g.used.has(id))continue;
   const o=m.orientations[oi];if(!o.cells.every(c=>(g.totals.get(pointKey(add(c.pos,translation)))??0)+c.weight<=m.capacity))continue;
   if(!markingSlots(o.marks).every(c=>{const old=g.section.get(`${pointKey(add(c.pos,translation))}|${c.component}`);return !old||old.value===JSON.stringify(c.value);}))continue;
   expected.add(id);
  }
  assert.deepEqual(new Set([...g.points.get(k).incident].filter(c=>c.valid).map(c=>c.id)),expected);
  const generations=g.selected.filter(c=>c.cells.some(p=>p.k===k)).map(c=>c.generation);
  assert.equal(Math.min(...g.generations.get(k).keys()),Math.min(...generations));
 }
}
const model=prepareModel({tile:'a2_hat_prism',mirrors:true,radius:18});
const g=new GrowthGraph(model,{fixed:[seed]});g.apply(seed,{root:true});
assert.ok(g.points.size<model.required.length,'No preactivated target window');
const root=digest(g);audit(g);
// Decision priority is global, not nearest-point or minimum-degree first.
const scheduleGraph=new GrowthGraph({capacity:2,orientations:[{cells:[{pos:[0,0,0],weight:1}],marks:[]}]});
for(const [k,degree,generation] of [['0,0,0',3,0],['1,0,0',1,2],['2,0,0',0,5]]){scheduleGraph.active.add(k);scheduleGraph.points.set(k,{k,pos:k.split(',').map(Number),degree});scheduleGraph.generations.set(k,new Map([[generation,1]]));}
assert.equal(scheduleGraph.schedule().kind,'dead');scheduleGraph.active.delete('2,0,0');assert.equal(scheduleGraph.schedule().point.k,'1,0,0');scheduleGraph.points.get('1,0,0').degree=2;assert.equal(scheduleGraph.schedule().point.k,'0,0,0');
let randomState=10;const random=()=>((randomState=Math.imul(randomState,1664525)+1013904223|0)>>>0)/4294967296;
const undos=[];
for(let n=0;n<30;n++){
 const s=g.schedule();if(s.kind==='dead'){g.rollback(undos.pop());continue;}
 const moves=orderGrowthCandidates(g,s.point,random);const before=digest(g),undo=g.apply(moves[0]);audit(g);g.rollback(undo);assert.equal(digest(g),before);audit(g);
 undos.push(g.apply(moves[0]));
}
while(undos.length)g.rollback(undos.pop());assert.equal(digest(g),root);audit(g);
// Extended markings conflict at a point outside all positive support, and
// rollback revives the rejected candidate. Individual '*' is unconstrained.
const marked={capacity:2,orientations:[
 {cells:[{pos:[0,0,0],weight:1}],marks:[{pos:[9,0,0],value:[0,'*']}]},
 {cells:[{pos:[0,0,0],weight:1}],marks:[{pos:[9,0,0],value:[1,2]}]},
 {cells:[{pos:[0,0,0],weight:1}],marks:[{pos:[9,0,0],value:['*',2]}]},
]};
const mg=new GrowthGraph(marked);const rootMove=mg.candidate(0,[0,0,0]),bad=mg.candidate(1,[0,0,0]);const mu=mg.apply(rootMove,{root:true});assert.equal(bad.valid,false);assert.ok(mg.markingCuts>0);audit(mg);mg.rollback(mu);assert.equal(bad.valid,true);assert.equal(mg.section.size,0);
const last=async stream=>{let result;for await(const e of stream)if(e.type==='result'||e.type==='finished'||e.type==='error')result=e;return result;};
// Goal checks cannot accept a root whose frontier has zero candidates.
const dead={capacity:2,orientations:[{cells:[{pos:[0,0,0],weight:1}],marks:[]}]};
const dr=await last(grow(dead,{targetTiles:1,timeMs:1000}));assert.equal(dr.result,'exhausted_seed');assert.equal(dr.verification.frontierViable,false);
// Matched seeds and policy: mode names alone cannot affect search without RL
// or a marking. Changing a distant display window does not affect growth.
const cube=prepareModel({tile:'cube',radius:1});
const collect=async(m,mode)=>{const events=[];for await(const e of grow(m,{mode,targetTiles:20,timeMs:10000,trace:true,seed:10}))events.push(e);return events;};
const a=await collect(cube,'free'),b=await collect({...cube,required:[{pos:[999,999,999],generation:0}]},'gcts');
assert.deepEqual(a.map(e=>[e.action,e.placements]),b.map(e=>[e.action,e.placements]));assert.equal(a.at(-1).result,'growth_checkpoint');assert.ok(verifyGrowth(cube,a.at(-1).placements).ok);
// Real cold learning is followed by real marked growth in the shared runner.
let learned,searchModel;const data={tile:'a2_hat_prism',mirrors:true,radius:1,searchProtocol:'seed-growth',targetTiles:20,seed:10,timeMs:20000,nodes:10000,pairNodes:500,markingExtent:0,mode:'gcts'};
let final;for await(const e of runExperiment(data)){if(e.type==='marking-learned')learned=e.marking;if(e.type==='model')searchModel=e.model;if(e.type==='result')final=e;if(e.type==='error')throw Error(e.message);}
assert.equal(learned.accepted,true);assert.equal(final.result,'growth_checkpoint');assert.ok(searchModel.orientations.some(o=>o.marks.length));assert.ok(verifyGrowth(searchModel,final.placements).ok);assert.equal(final.stats.searchProtocol,'seed-growth');
const learnedGraph=new GrowthGraph(searchModel,{fixed:[seed]});learnedGraph.apply(seed,{root:true});
for(let n=0;n<10;n++){const s=learnedGraph.schedule();if(!s.point||s.kind==='dead')break;const before=digest(learnedGraph),c=orderGrowthCandidates(learnedGraph,s.point,random)[0],undo=learnedGraph.apply(c);audit(learnedGraph);learnedGraph.rollback(undo);assert.equal(digest(learnedGraph),before);audit(learnedGraph);learnedGraph.apply(c);}

// V1 count mode dispatches to the same protocol, rather than its geometric
// heuristics. Its non-count/structural controls remain explicitly separate.
const legacy=await last(createTilingStream({mode_key:'cube',search_protocol:'seed-growth',tiling_strategy:'free_range',criterion:'count',target_val:20,random_seed:10,time_limit_ms:10000,include_mirrors:false},tileSpecs));
assert.equal(legacy.success,true);assert.equal(legacy.search_stats.search_protocol,'seed-growth');assert.equal(legacy.tile_count,20);assert.equal(legacy.tiling_evidence.certified,false);
console.log('PASS growth: exhaustive frontier domains, generation rollback, marking-only conflict/wildcards, seed viability, window independence, matched no-marking traces, cold learned growth and legacy dispatch.');

// Differential check against the actual article engine, on the same one-cap
// Hat point model. This prefix reaches ten tiles without a failed branch;
// deeper memoization traces are not asserted identical.
globalThis.requestAnimationFrame=cb=>setTimeout(cb,0);
const os=tileOrientations('hat',A2_TILE_LOOPS.hat),on=p=>(p[0]-p[1])%3===0&&(p[1]-p[2])%3===0;
const reference=await solveA2Tiling({boundary:[[20,0,-20],[0,20,-20],[-20,20,0],[-20,0,20],[0,-20,20],[20,-20,0]],initialPlacements:[{tile:'hat',orientation:os[0],translation:[0,0,0]}],fixedInitialPlacements:true,completePointGrowth:true,latticePointFilter:on,maximize:true,targetPlacements:10,tiles:['hat'],randomSeed:10,marking:new NoA2Marking(),nodeLimit:1000});
const planar={capacity:12,orientations:os.map(o=>({cells:[...o.occupancy.values()].filter(c=>on(c.point)).map(c=>({pos:c.point,weight:c.weight})),marks:[]})),placementDomain:{kind:'a2_slab',index3:true}};
const parallel=await last(grow(planar,{targetTiles:10,timeMs:10000,seed:10}));
assert.deepEqual(parallel.placements.map(p=>[p.oi,p.translation]),reference.placements.map(p=>[p.orientation.index,p.translation]));assert.equal(parallel.stats.attempts,reference.stats.nodes);
const slab=await last(grow(model,{targetTiles:10,timeMs:10000,seed:10}));
assert.deepEqual(slab.placements.map(p=>[p.oi,p.translation]),parallel.placements.map(p=>[p.oi,p.translation]));
console.log('PASS direct GCTS-I ten-tile unmarked Hat prefix, including the two-cap slab lift.');
