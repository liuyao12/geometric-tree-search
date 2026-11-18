import assert from 'node:assert/strict';
import {selectPointBranch} from '../assets/gcts-point-branching.js';
import {createFrontierGraph} from '../assets/tiling-frontier-graph.js';
import {CoronaGraph} from '../apps/3d-lattice-tiler/corona-graph.js';
import {GrowthGraph,grow,verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
import {PointGraph,search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {JSearch} from '../assets/j-tiling-engine.js';
import {solveA2Tiling,NoA2Marking,tileOrientations} from '../assets/a2-tiling-engine.js';

const [a,b,c,d,e]=['a','b','c','d','e'].map(id=>({id}));
const point=(key,introducedAt,legal)=>({key,introducedAt,legal});
const frontier=[point('p',0,[a,b]),point('q',0,[a,c]),point('later',3,[d,e])];
const selected=selectPointBranch(frontier,()=>0,{isAdjacent:move=>move===c||move===d});
assert.deepEqual(selected.moves.map(move=>move.placement.id),['c','a']);
assert.ok(selected.moves.every(move=>move.frontier.key==='q'));
assert.equal(selected.moves[1].placement,a,'Non-neighbor siblings remain available.');
const forced=selectPointBranch([...frontier,point('late-forced',10,[e])],()=>assert.fail('Forced propagation must precede random selection.'));
assert.equal(forced.moves[0].placement,e);
const dead=selectPointBranch([...frontier,point('dead',9,[])],()=>assert.fail('Dead point check must precede selection.'));
assert.equal(dead.dead.key,'dead');
assert.equal(selectPointBranch([],()=>0).moves.length,0);
for(const pick of [0,.2,.5,.9,.999]){
  const full=selectPointBranch(frontier,()=>pick,{restrictToPoint:false});
  assert.equal(full.moves.length,3,'Candidates shared by points count once.');
  const fixed=selectPointBranch(frontier,()=>pick);
  assert.equal(fixed.moves[0].placement.id,full.moves[0].placement.id);
  assert.ok(fixed.moves.every(move=>move.frontier===fixed.moves[0].frontier));
  assert.deepEqual(new Set(fixed.moves.map(move=>move.placement.id)),new Set(fixed.moves[0].frontier.legal.map(move=>move.id)));
}

const A={id:'A',vertices:['p','q']},B={id:'B',vertices:['p']},C={id:'C',vertices:['q']},D={id:'D',vertices:['r']},E={id:'E',vertices:['r']};
const graph=createFrontierGraph({random:()=>0,enumerate:p=>({p:[A,B],q:[A,C],r:[D,E]})[p.key],legal:()=>true,compatibleWithAddition:()=>true,footprint:()=>({x0:0,x1:1,y0:0,y1:1})});
graph.build([{key:'p',depth:100,total:1},{key:'q',depth:100,total:1}]);
const original=graph.inspect();
const delta=graph.push({vertices:['q']},[{key:'p',depth:100,total:1},{key:'q',depth:100,total:1},{key:'r',depth:0,total:1}]);
assert.equal(graph.inspect().find(p=>p.key==='r').introducedAt,1);
assert.notEqual(graph.choose().point.key,'r','A newer point cannot outrank an older point, regardless of geometric generation.');
graph.pop(delta);
assert.deepEqual(graph.inspect(),original);

// Arbitrary point weights and supports, with no polygon or edge data.
const model={capacity:2,orientations:[{cells:[{pos:[0,0,0],weight:1},{pos:[4,0,0],weight:1}],marks:[]}]};
for(const Graph of [CoronaGraph,GrowthGraph]){
  const g=new Graph(model),root=g.apply({oi:0,translation:[0,0,0]},{root:true});
  const before=[...g.introducedAt],choice=g.schedule(()=>0);
  assert.equal(choice.kind,'forced');
  const child=g.apply(choice.candidates[0]);
  assert.ok([...g.introducedAt.values()].includes(1));
  g.audit();g.rollback(child);g.audit();
  assert.deepEqual([...g.introducedAt],before);
  g.rollback(root);
  assert.equal(g.introducedAt.size,0);
}
let growthResult;
for await(const event of grow(model,{targetTiles:8,nodes:200,timeMs:2000,seed:42,audit:true}))growthResult=event;
assert.equal(growthResult.result,'growth_checkpoint');
assert.ok(verifyGrowth(model,growthResult.placements).ok);

const finite={capacity:1,required:[{pos:[0,0,0]},{pos:[1,0,0]}],
  orientations:[0,1].map(()=>({cells:[{pos:[0,0,0],weight:1}],marks:[]}))};
const windowGraph=new PointGraph(finite);
const finiteChoice=windowGraph.schedule(()=>0);
assert.equal(finiteChoice.kind,'branch');
assert.equal(finiteChoice.candidates.length,2);
let result;
for await(const event of search(finite,{seed:43,nodes:200,timeMs:2000}))result=event;
assert.equal(result.result,'finite_exact');
assert.ok(verify(finite,result.placements).ok);

const j=new JSearch({target:10,nodeLimit:500,audit:true});
const choice=j.choice(),fingerprint=j.fingerprint();
assert.ok(choice.candidates.length);
assert.ok(choice.candidates.every(c=>c.corners.some(p=>p.key===choice.row.key)));
const candidate=choice.candidates[0],undo=j.apply(candidate,1);
j.auditGraph();j.undo(undo);j.auditGraph();
assert.equal(j.fingerprint(),fingerprint);
while(j.step().done===false){}
assert.equal(j.status,'consistent finite patch');
const triangle=[[0,0,0],[1,0,-1],[0,1,-1]];
const blockedCheckpoint=await solveA2Tiling({
  boundary:triangle,tiles:['triangle'],customTiles:{triangle},
  initialPlacements:[{tile:'triangle',orientation:tileOrientations('triangle',triangle)[0],translation:[0,0,0]}],
  maximize:true,targetPlacements:1,fixedInitialPlacements:true,
  placementFilter:()=>false,marking:new NoA2Marking()
});
assert.equal(blockedCheckpoint.result,'no','A growth checkpoint must detect a dead frontier before declaring success.');
console.log('ok: global propagation, chronological point ages, adjacency preference, fixed-point siblings, and rollback across point engines');
