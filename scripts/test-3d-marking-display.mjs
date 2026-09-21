import assert from 'node:assert/strict';
import {placedMarkingPoints,applyMarkingUpdates,markingPointKey} from '../apps/3d-lattice-tiler/marking-display.js';
import {LearnedSection} from '../apps/3d-lattice-tiler/marking-learning.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {learnMarking} from '../apps/3d-lattice-tiler/marking-learning.js';
import {search} from '../apps/3d-lattice-tiler/v2/search.js';
const model={orientations:[{type:0,index:0,marks:[{pos:[0,0,0],value:[null,0,'*']},{pos:[1,0,0],value:0}]}]};
const placements=[{oi:0,translation:[0,0,0]},{oi:0,translation:[1,0,0]}];
assert.deepEqual(placedMarkingPoints(model,placements).map(p=>[p.pos,p.component,p.value,p.count]),[
 [[0,0,0],1,0,1],[[1,0,0],0,0,1],[[1,0,0],1,0,1],[[2,0,0],0,0,1]
]);
const scalar={orientations:[{type:0,index:0,marks:[{pos:[0,0,0],value:7},{pos:[1,0,0],value:7}]}]};
const section=new LearnedSection(scalar,{fields:scalar.orientations.map(o=>o.marks)}),display=new Map();
const moves=placements.map(p=>({type:0,index:0,translation:p.translation}));
const sorted=points=>[...points].sort((a,b)=>markingPointKey(a).localeCompare(markingPointKey(b)));
for(let i=0;i<2;i++){
 section.add(moves[i]);applyMarkingUpdates(display,section.updates(moves[i]));
 assert.deepEqual(sorted(display.values()),sorted(placedMarkingPoints(scalar,placements.slice(0,i+1))));
 assert.deepEqual(sorted(display.values()),sorted(section.points()));
}
assert.equal(display.get('1,0,0|0').count,2);
for(let i=1;i>=0;i--){section.remove(moves[i]);applyMarkingUpdates(display,section.updates(moves[i]));assert.deepEqual(sorted(display.values()),sorted(section.points()));}
assert.equal(display.size,0);
// Actual nontrivial browser learner: every displayed value and overlap must be
// the one used by the matcher, including exterior-only assigned points.
let learned;for await(const e of learnMarking(prepareModel({tile:'a2_turtle_prism',radius:1,mirrors:true}),{timeMs:30000}))learned=e;
assert.ok(learned.marking.accepted);let result;for await(const e of search(learned.model,{mode:'gcts',learnedRestriction:true,timeMs:5000,nodes:10000}))result=e;
assert.equal(result.result,'finite_exact');const rows=placedMarkingPoints(learned.model,result.placements);
assert.ok(rows.length);assert.ok(rows.some(p=>p.count>1));
const expected=result.placements.reduce((n,p)=>n+learned.marking.fields[p.oi].length,0);
assert.equal(rows.reduce((n,p)=>n+p.count,0),expected);
console.log('PASS assigned zero, component wildcards, overlapping agreement, section rollback, and actual Turtle learned tiling values.');
// A synthetic constant-zero field exercises legacy display transport. It is a
// test control, not a bundled learned result; the production cube learns *.
const {preprocessTilingSystem,legacyMarkingModel,createTilingStream,tileSpecs}=await import('../apps/3d-lattice-tiler/engine.js');
const {markingSystem}=await import('../apps/3d-lattice-tiler/marking-storage.js');
const config={mode_key:'cube',tiling_strategy:'learning_free_range',gcts_failure_marking:true,complete_lattice_point_branching:true,criterion:'count',target_val:8,time_limit_ms:5000,node_limit:1000,placement_details:true};
const legacyModel=legacyMarkingModel(preprocessTilingSystem(config,tileSpecs));
let cube;for await(const e of learnMarking(legacyModel,{timeMs:10000}))cube=e.marking;
cube.fields=legacyModel.orientations.map(o=>o.cells.map(c=>({pos:c.pos,component:0,value:0})));
const entry={domain:markingSystem(legacyModel),marking:cube},live=new Map();let marked=false,deltas=0;
for await(const e of createTilingStream({...config,savedMarking:entry},tileSpecs)){
 if(e.type==='marking-learned')marked=true;
 if(e.type==='full_update'&&marked){
  const chosen=e.placements.map(p=>({oi:legacyModel.orientations.findIndex(o=>o.type===p.prototile_idx&&o.index===p.orientation_index),translation:p.translation}));
  const expected=placedMarkingPoints({...legacyModel,orientations:legacyModel.orientations.map((o,i)=>({...o,marks:cube.fields[i]}))},chosen);
  assert.deepEqual(sorted(e.marking_points),sorted(expected));
  if(deltas)assert.deepEqual(sorted(live.values()),sorted(expected));
  live.clear();applyMarkingUpdates(live,e.marking_points);
 }
 if(e.type==='placement_delta'&&marked){applyMarkingUpdates(live,e.marking_updates);deltas++;}
}
assert.ok(deltas);assert.ok(live.size);console.log('PASS v1 actual section snapshots and incremental display updates match independent placement replay.');
