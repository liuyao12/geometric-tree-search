import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {POINT_GROUP,transform,orient,transformedPlacement,composeIndex,compilePatchConstraints,ConstraintSection} from '../apps/3d-lattice-tiler/patch-constraint-markings.js';
const file='data/nonacube-patch-constraints/study.json',bytes=fs.readFileSync(file),data=JSON.parse(bytes);
const key=p=>p.join(','),plus=(a,b)=>a.map((v,i)=>v+b[i]);
function cells([oi,t]){const normal=[2,1,0][oi],v=[t];for(let axis=0;axis<3;axis++)if(axis!==normal)for(const d of [-2,-1,1,2]){const q=[...t];q[axis]+=d;v.push(q);}return v;}
function halo(vs){const r=new Set();for(const p of vs)for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)r.add(key(plus(p,[x,y,z])));return r;}
function pack(placements){const occupied=new Set();for(const s of placements)for(const p of cells(s)){assert(!occupied.has(key(p)),'Overlapping positive witness');occupied.add(key(p));}return occupied;}
const core=pack(data.fixed),q=data.deadPoint;assert(!core.has(key(q)));assert(halo(data.fixed.flatMap(cells)).has(key(q)));
const covering=new Map();
for(let oi=0;oi<3;oi++)for(const anchor of cells([oi,[0,0,0]])){
  const s=[oi,q.map((v,i)=>v-anchor[i])],vs=new Set(cells(s).map(key));
  const blocked=data.fixed.map((t,i)=>cells(t).some(p=>vs.has(key(p)))?i:null).filter(x=>x!==null);
  assert(blocked.length>0);covering.set(JSON.stringify(s),blocked);
}
assert.equal(covering.size,27);assert.equal(data.coverBlockers.length,27);
assert.equal(new Set(data.coverBlockers.map(row=>JSON.stringify(row.placement))).size,27);
for(const row of data.coverBlockers)assert.deepEqual(row.roles,covering.get(JSON.stringify(row.placement)));
assert.deepEqual(data.pairs.map(p=>p.roles),[[0,1],[0,2],[1,2]]);
for(const pair of data.pairs){
  assert.equal(pair.status,'SAT');assert.deepEqual(pair.fixed,pair.roles.map(i=>data.fixed[i]));
  const occupied=pack([...pair.fixed,...pair.outer]),required=halo(pair.fixed.flatMap(cells));
  assert([...required].every(k=>occupied.has(k)),'Incomplete pair surround');
}
const full=(1<<data.marking.fiberStates)-1,allowed=data.marking.allowedMasks;
function accepts(rows,mask,universe){let intersection=universe;rows.forEach((v,i)=>{if(mask&(1<<i))intersection&=v;});return !!intersection;}
for(let mask=0;mask<8;mask++)assert.equal(accepts(allowed,mask,full),mask!==7);
// Independent exhaustive check of the claimed one- and two-state failures.
for(const rank of [1,2]){const u=(1<<rank)-1;let possible=false;for(let a=0;a<=u;a++)for(let b=0;b<=u;b++)for(let c=0;c<=u;c++)if(Array.from({length:8},(_,s)=>accepts([a,b,c],s,u)===(s!==7)).every(Boolean))possible=true;assert(!possible);}
const marking=compilePatchConstraints(data.fixed,q,data.marking);
for(const pair of data.pairs){
  const section=new ConstraintSection(marking,{requiredPoints:halo(pair.fixed.flatMap(cells))});
  [...pair.fixed,...pair.outer].forEach(s=>section.push(s));
  assert.equal(section.conflicts().length,0,'Marking rejects a certified finite surround');
}
assert.equal(marking.fields.flat().length,144);
const atoms=new Set(marking.fields.flatMap((f,oi)=>f.map(a=>JSON.stringify([oi,a.pos,a.channel,a.allowed,a.role]))));
for(let gi=0;gi<48;gi++){
  const g=POINT_GROUP[gi];assert.equal(new Set(marking.componentAction[gi]).size,48);
  for(let oi=0;oi<3;oi++)for(const atom of marking.fields[oi])assert(atoms.has(JSON.stringify([orient(g,oi),transform(g,atom.pos),marking.componentAction[gi][atom.channel],atom.allowed,atom.role])),'Noncovariant field');
  for(let hi=0;hi<48;hi++){
    const h=POINT_GROUP[hi],gh=composeIndex(g,h);
    for(const e of [[1,0,0],[0,1,0],[0,0,1]])assert.deepEqual(transform(g,transform(h,e)),transform(POINT_GROUP[gh],e));
    for(let j=0;j<48;j++)assert.equal(marking.componentAction[gi][marking.componentAction[hi][j]],marking.componentAction[gh][j]);
  }
}
// Each channel has exactly one role-specific atom in each of the three
// orientations. At a common site these uniquely reconstruct a translated
// symmetry copy of the training patch: no unrelated pattern can trigger it.
for(let ch=0;ch<48;ch++){
  const rows=marking.fields.flatMap((f,oi)=>f.filter(a=>a.channel===ch).map(a=>({oi,...a})));
  assert.equal(rows.length,3);assert.equal(new Set(rows.map(a=>a.oi)).size,3);
  for(const atom of rows){const expected=transformedPlacement(POINT_GROUP[ch],data.fixed[atom.role]);assert.equal(atom.oi,expected[0]);assert.deepEqual(atom.pos,transform(POINT_GROUP[ch],q).map((v,i)=>v-expected[1][i]));}
}
let subsetCases=0;
for(const g of POINT_GROUP)for(const shift of [[0,0,0],[5,-4,2],[-6,3,-1]])for(let mask=0;mask<8;mask++){
  const fixed=data.fixed.map(s=>{const [oi,t]=transformedPlacement(g,s);return [oi,plus(t,shift)];}),section=new ConstraintSection(marking);
  const saved=[];fixed.forEach((s,i)=>{if(mask&(1<<i)){saved.push(section.snapshot());section.push(s);}});
  assert.equal(section.conflicts().length>0,mask===7);
  if(mask===7)assert(section.conflicts().some(c=>key(c.point)===key(plus(transform(g,q),shift))));
  while(saved.length){section.pop();assert.deepEqual(section.snapshot(),saved.pop());}subsetCases++;
}
const guard=new ConstraintSection(marking,{requiredPoints:new Set()});data.fixed.forEach(s=>guard.push(s));assert.equal(guard.conflicts().length,0);
guard.requiredPoints.add(key(q));assert(guard.conflicts().length>0);
// The direct fixed-value equality target is impossible independently of rank:
// every unequal pair of contributions is contained in a proper pair subset.
const receipt={verified:true,studySHA256:crypto.createHash('sha256').update(bytes).digest('hex'),
  blockedCoverPlacements:covering.size,verifiedPairSurrounds:data.pairs.length,guardedPairSurroundsAccepted:true,
  subsetSymmetryTranslationChecks:subsetCases,groupSize:48,prototypeAssignments:144,
  exactRollback:true,equivariant:true,noRejectionOutsideCertifiedPatternOrbit:true,
  finiteBoundaryGuard:true,semantics:'Proposed constraint-valued section; existing fixed-value markings unchanged.',
  limitations:['Only one minimal triple, not a complete catalogue.','Not integrated into the production GCTS learner.','No search-speedup claim.','Finite-corona use requires the transformed dead cell to be required.']};
if(process.argv.includes('--receipt'))fs.writeFileSync('data/nonacube-patch-constraints/verification.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt));
