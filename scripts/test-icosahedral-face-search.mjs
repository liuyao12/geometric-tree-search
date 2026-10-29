import assert from 'node:assert/strict';
import {FaceSearch,faceAttachments,faceKey,pairRelation,compatiblePair,prepare,chooseFace,intersectionVertices} from '../assets/icosahedral-face-search.js';
import {ORIENTATIONS,makeRhombohedron} from '../assets/icosahedral-exact.js';
import {ONE,vector,vadd,vsub,vscale,dot,cross,inverseColumns,pointKey} from '../assets/golden-field.js';

// An independent enumeration of EVERY proper rigid full-face isometry from
// both prototypes. It does not assume that the resulting vertices use STAR.
let isometries=0;
const prototypes=['prolate','oblate'].map(k=>ORIENTATIONS.find(t=>t.kind===k));
for(const owner of ORIENTATIONS)for(let fi=0;fi<6;fi++){
 const target=owner.faces[fi].map(i=>owner.vertices[i]);
 const n=cross(vsub(target[1],target[0]),vsub(target[3],target[0]));
 const actual=new Set();
 for(const source of prototypes)for(const face of source.faces){
  const points=face.map(i=>source.vertices[i]),a=points[0],u=vsub(points[1],a),v=vsub(points[3],a),normal=cross(u,v),inverse=inverseColumns(u,v,normal);
  for(let corner=0;corner<4;corner++)for(const direction of [-1,1]){
   const origin=target[corner],tu=vsub(target[(corner+direction+4)%4],origin),tv=vsub(target[(corner-direction+4)%4],origin),tn=vscale(n,-1n);
   if(!dot(u,v).equals(dot(tu,tv))||dot(cross(tu,tv),tn).sign()<0)continue;
   assert(dot(normal,normal).equals(dot(tn,tn)));
   const transformed=source.vertices.map(p=>{const delta=vsub(p,a);return [tu,tv,tn].reduce((s,e,i)=>vadd(s,vscale(e,dot(inverse[i],delta))),origin);});
   actual.add(transformed.map(pointKey).sort().join('|'));isometries++;
  }
 }
 const candidates=faceAttachments(owner,fi);
 assert.equal(candidates.length,4);assert.equal(candidates.filter(t=>t.kind==='prolate').length,2);
 assert.deepEqual(new Set(candidates.map(t=>t.id)),actual,'The 20 orientations must close under all proper face attachments');
 for(const tile of candidates)assert.equal(pairRelation(owner,tile),'common-face');
}
const t=ORIENTATIONS[0],e=t.edges;
assert.equal(pairRelation(t,t),'overlap');
assert.equal(pairRelation(t,makeRhombohedron(t.axes,e[0])),'common-face');
assert.equal(pairRelation(t,makeRhombohedron(t.axes,vadd(e[0],e[1]))),'common-face');
assert.equal(pairRelation(t,makeRhombohedron(t.axes,e.reduce(vadd,vector(0n,0n,0n)))),'common-face');
assert.equal(pairRelation(t,makeRhombohedron(t.axes,vadd(e[0],vscale(e[1],ONE.div(2n))))),'partial-contact');
assert.equal(pairRelation(t,makeRhombohedron(t.axes,vscale(e[0],3n))),'disjoint');
const p=(key,generation,n)=>({key,generation,candidates:new Set(Array.from({length:n},(_,i)=>String(i)))});
assert.equal(chooseFace(new Map([['a',p('a',0,1)],['b',p('b',9,0)]])).kind,'dead');
assert.equal(chooseFace(new Map([['a',p('a',0,3)],['b',p('b',9,1)]])).point.key,'b');
assert.equal(chooseFace(new Map([['a',p('a',0,4)],['b',p('b',9,2)]])).point.key,'a');
const search=new FaceSearch({seed:4,target:60,budget:300});
const initial=search.inspect(),checkpoint=search.trail.length;
search.apply([...search.candidates.values()].find(c=>c.legal).tile);search.undo(checkpoint);
assert.deepEqual(search.inspect(),initial,'All indexes, incidence and generation data restore exactly');
function oracle(s){
 const placed=[...s.placed.values()].map(r=>r.tile);
 for(const point of s.frontier.values()){
  const expected=faceAttachments(point.owner.tile,point.owner.faceIndex).filter(c=>!s.candidates.get(c.id)?.excluded&&!s.placed.has(c.id)&&placed.every(t=>compatiblePair(c,t))).map(t=>t.id).sort();
  assert.deepEqual([...point.candidates].sort(),expected,'Incremental domains must equal exhaustive full-patch re-enumeration');
 }
}
for(let i=0;i<14;i++){oracle(search);search.step();}
while(!['checkpoint','budget','exhausted'].includes(search.state))search.step();
assert.equal(search.state,'checkpoint');assert.equal(search.placed.size,60);assert.equal(search.summary().dead,0);assert(search.stats.backtracks>0);assert(search.stats.forced>0);oracle(search);
const placed=[...search.placed.values()].map(r=>r.tile);
for(let i=0;i<placed.length;i++)for(let j=i+1;j<placed.length;j++){
 assert(compatiblePair(placed[i],placed[j]));
 // Independent contact certificate, bypassing SAT and spatial indexes.
 const vertices=intersectionVertices(placed[i],placed[j]);
 if(vertices.length){const key=vertices.map(pointKey).sort().join('|');assert(prepare(placed[i]).features.has(key)&&prepare(placed[j]).features.has(key));}
}
const a=new FaceSearch({target:12,seed:19}),b=new FaceSearch({target:12,seed:19});
for(let i=0;i<8;i++){a.step();b.step();}assert.deepEqual(a.inspect(),b.inspect());
const limited=new FaceSearch({target:60,budget:1});limited.step();limited.step();assert.equal(limited.state,'budget');assert.equal(limited.export().result,'unknown');
console.log(`ok: ${isometries} exact rigid face isometries; 120 complete four-candidate domains; exact contacts and T-junction rejection; exhaustive graph oracle; full rollback; 60-tile replay with ${search.stats.backtracks} backtrack(s)`);
