import assert from 'node:assert/strict';
import {tiles} from '../apps/a2-online-tiler/companions.js';
import {board,tileSet} from '../apps/a2-online-tiler/companion-model.js';
import {onlineMarks} from '../apps/a2-online-tiler/companion-learning.js';
import {runExperiment} from '../apps/a2-online-tiler/companion-run.js';
import {minus,worldMark} from '../research/deterministic-a2/model.mjs';
import {fill,rng} from '../research/deterministic-a2/search.mjs';

const ids=['hat','turtle','K6-074'];
function contains(loop,x,y) {
  let inside=false;
  for(let i=0,j=loop.length-1;i<loop.length;j=i++) {
    const [a,b]=loop[i],[u,v]=loop[j];
    if((b>y)!==(v>y) && x<(u-a)*(y-b)/(v-b)+a) inside=!inside;
  }
  return inside;
}
function verifyBoard(frame) {
  const all=new Map();
  // Generate grid cells independently; their interior lattice sites never lie on a grid edge.
  for(let h=-9;h<=9;h++) for(let k=-9;k<=9;k++) {
    for(const [dx,dy] of [[1,0],[0,1],[-1,1],[-1,0],[0,-1],[1,-1]]) {
      const x=2*h-2*k+dx,y=2*h+4*k+dy;
      const hit=frame.placements.filter(p=>contains(p.loop,x,y));
      assert.ok(hit.length<=1,'polygons overlap');
      if(Math.max(Math.abs(h),Math.abs(k),Math.abs(h+k))<=frame.ring) assert.equal(hit.length,1);
      if(hit.length) all.set(hit[0],(all.get(hit[0])??0)+1);
    }
  }
  const marks=new Map();
  for(const p of frame.placements) {
    assert.equal(all.get(p),tiles.find(t=>t.id===p.tile).cells.length);
    for(const [x,y,axis,v] of p.marks) {
      const key=[x,y,axis].join();
      if(marks.has(key)) assert.equal(marks.get(key),v);
      marks.set(key,v);
    }
  }
}
for(const learning of [false,true]) {
  let result;
  runExperiment({ids,first:'hat',radius:2,seed:6,learning},frame=>{
    if(frame.status==='covered' || frame.status==='ring') {result=frame;verifyBoard(frame);}
  });
  assert.equal(result.ring,2);
  assert.equal(result.assignments>0,learning);
}
for(const tile of tiles) {
  const model=tileSet([tile.id]),root=model.types.get(tile.id).root;
  for(const row of root.rows) assert.ok(model.incident(row.point).includes(root));
}

// Replay every induced mismatch in a learned mixed table, independently
// enumerating relative poses and solving their unmarked finite obligations.
const model=tileSet(ids),root=model.types.get('hat').root,learned=onlineMarks(model),memo=new Set();
let result;
do {
  result=fill(model,board(1),[root],[...learned.table.values()],rng(6),1000,learned.consider,memo);
} while(result.status==='revised');
assert.equal(result.status,'covered');
assert.ok(learned.table.size>0);
const checked=new Set();
for(const a of learned.table.values()) for(const b of learned.table.values()) {
  const fixed=model.types.get(a.tile).root,world=worldMark(fixed,a),type=model.types.get(b.tile);
  for(const form of type.forms) {
    const rotated=worldMark({form,shift:[0n,0n,0n]},b);
    if(rotated.axis!==world.axis || rotated.value===world.value) continue;
    const shift=minus(world.point,rotated.point);
    if(!model.allowed(form,shift)) continue;
    const p=type.pose(form,shift),key=fixed.id+'|'+p.id;
    if(fixed.id===p.id || checked.has(key)) continue;
    checked.add(key);
    const targets=[...fixed.rows,...p.rows].map(r=>r.point);
    assert.equal(fill(model,targets,[fixed,p],[],rng(1),0).status,'exhausted',key);
  }
}
assert.ok(checked.size>0);
console.log('Verified exact covers in both modes and',checked.size,'unmarked pair certificates.');
