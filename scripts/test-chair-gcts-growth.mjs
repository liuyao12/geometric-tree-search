import assert from 'node:assert/strict';
import { VARIANTS, BASE_MARKS, CHILDREN, ROTATIONS, chairLeaves, verifyPatch, childSupertile,
  parentContainingChild, IDENTITY, key, add, COLORS } from '../3d-reptiles/chair/chair44.js';
import { createGrowthState, enumerateGrowthCandidates, growOne, shrinkOne, selectFrontier } from '../3d-reptiles/chair/chair-gcts.js';

assert.equal(BASE_MARKS.length,24);
assert.deepEqual(Object.fromEntries(Object.keys(COLORS).map(c=>[c,BASE_MARKS.filter(m=>m.color===c).length])),{red:8,green:8,blue:8});
assert.equal(VARIANTS.length,24);
const signatures = VARIANTS.map(v => JSON.stringify(v.marks.map(m => JSON.stringify(m)).sort()));
assert.equal(new Set(signatures).size,24);
assert.equal(CHILDREN.length,8);

// Independent panel-contact verifier: compare actual outward normals, colors
// and tangent arrows, not the production equality encoding.
function independent(placements, mirror=false) {
  const cells=new Set(),faces=new Map(); let contacts=0;
  for(let i=0;i<placements.length;i++) {
    const p=placements[i],v=VARIANTS[p.variantId];
    const point=c=>add(mirror&&i===1?[1-c[0],c[1],c[2]]:c,p.origin);
    const vector=c=>mirror&&i===1?[-c[0],c[1],c[2]]:c;
    for(const c of v.cells){const k=key(point(c));if(cells.has(k))return false;cells.add(k);}
    for(const m of v.marks){
      const c=point(m.cell),n=vector(m.direction),arrow=vector(m.arrow);
      const k=key(c.map((x,j)=>2*x+1+n[j]));
      const other=faces.get(k);
      if(other){
        contacts++;
        if(!n.every((x,j)=>x===-other.n[j])||key(arrow)!==key(other.arrow))return false;
        if(!((m.color==='blue'&&other.color==='blue')||(m.color==='red'&&other.color==='green')||(m.color==='green'&&other.color==='red')))return false;
      }
      faces.set(k,{n,arrow,color:m.color});
    }
  }
  return {cells,contacts};
}
for(let level=0;level<=3;level++) {
  const leaves=chairLeaves(level), checked=independent(leaves);
  assert.ok(checked);assert.ok(verifyPatch(leaves).valid);
  assert.equal(checked.cells.size,7*8**level);
  const size=2**(level+1);
  for(let x=0;x<size;x++) for(let y=0;y<size;y++) for(let z=0;z<size;z++)
    assert.equal(checked.cells.has(key([x,y,z])),x<size/2||y<size/2||z<size/2);
}
// Every retained outer child preserves its full decorated orientation, not
// just the missing corner; no reflections may sneak into inflation.
for(const rotation of ROTATIONS) for(const i of [0,1,2,3,5,6,7]) {
  const child={origin:[-3,7,2],rotation,size:8};
  const parent=parentContainingChild(child,i), recovered=childSupertile(parent,i);
  assert.deepEqual(recovered.origin,child.origin);assert.deepEqual(recovered.rotation,rotation);
  assert.ok(independent(chairLeaves(2,child.origin,rotation)));
}
const seed={variantId:0,origin:[0,0,0]},neighbors=new Set();
for(const v of VARIANTS) for(let x=-2;x<=2;x++) for(let y=-2;y<=2;y++) for(let z=-2;z<=2;z++) {
  const p={variantId:v.id,origin:[x,y,z]},pair=[seed,p];
  const test=independent(pair); if(test&&test.contacts)neighbors.add(`${v.id}@${key(p.origin)}`);
}
assert.equal(neighbors.size,44,'Chair44 must admit exactly 44 face-adjacent neighbors');
const point=(id,generation,degree)=>({id,generation,candidates:new Set(Array.from({length:degree},(_,i)=>i))});
const early=point('early',0,5),later=point('later',2,2),forced=point('forced',9,1),dead=point('dead',10,0);
assert.equal(selectFrontier([early,later,forced,dead]).selected,dead);
assert.equal(selectFrontier([early,later,forced]).selected,forced);
assert.equal(selectFrontier([later,early]).selected,early);
// A genuinely nonoverlapping, arrow-compatible pair that leaves a dead cell.
// Inject a branch frame to exercise recovery, not only user-initiated undo.
const root=createGrowthState(),rootGraph=enumerateGrowthCandidates(root);
const bad={variantId:1,origin:[0,0,2],generation:1};
assert.ok(independent([...root.placements,bad]));
const doomed={...root,placements:[...root.placements,bad],stack:[{placements:root.placements,remaining:[rootGraph.candidates[0]]}]};
assert.ok(enumerateGrowthCandidates(doomed).dead);
const recovered=growOne(doomed);
assert.ok(recovered.solverBacktracks>0);
assert.ok(independent(recovered.placements));
assert.equal(enumerateGrowthCandidates(recovered).dead,false);
assert.strictEqual(shrinkOne(recovered),doomed);
let state=createGrowthState();
const graph=enumerateGrowthCandidates(state);
assert.deepEqual(new Set(graph.candidateNodes.keys()),neighbors,'Full graph agrees with independent exhaustive enumeration');
for(const [id,c] of graph.candidateNodes)for(const [p,node] of graph.frontier)
  assert.equal(node.candidates.has(id),c.cells.includes(p),'Incidence must be complete in both directions');
for(let step=0;step<100&&!state.complete;step++) {
  const before=state;state=growOne(state);
  assert.ok(independent(state.placements));
  assert.strictEqual(shrinkOne(state),before,'Undo restores complete state including generations and branch alternatives');
}
assert.equal(state.placements.length,64);assert.equal(state.status,'consistent finite patch');
assert.equal(enumerateGrowthCandidates(state).dead,false,'Checkpoint must not hide any frontier dead end');
console.log('Chair44 passed: 24 panels, 24 proper rotations, 44 neighbors, three inflation levels, complete graph, rollback, 64-chair growth.', {forced:state.forcedPlacements,branches:state.branchDecisions,backtracks:state.solverBacktracks});
