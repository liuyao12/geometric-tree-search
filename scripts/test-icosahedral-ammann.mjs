import assert from 'node:assert/strict';
import { AMMANN_ORIENTATIONS,decorateGeometry,pointMarkingsAgree,translatedDecoration } from '../assets/icosahedral-ammann-markings.js';
import { FaceSearch,faceAttachments,compatiblePair,prepare } from '../assets/icosahedral-face-search.js';
import { STAR,makeRhombohedron,makeIcosahedralPatch } from '../assets/icosahedral-exact.js';
import { vector,vadd,vsub,dot,pointKey } from '../assets/golden-field.js';
assert.equal(AMMANN_ORIENTATIONS.length,120);
for(const kind of ['prolate','oblate'])for(const hand of ['left','right'])assert.equal(AMMANN_ORIENTATIONS.filter(t=>t.kind===kind&&t.decoration.hand===hand).length,30);
for(const tile of AMMANN_ORIENTATIONS){
 assert.equal(decorateGeometry(tile.geometry).length,6);
 for(let i=0;i<6;i++)for(const [color,expected]of [['black',-1],['red',1]]){
  const corner=tile.faceDots[i][`${color}Corner`],f=tile.faces[i].map(j=>tile.vertices[j]),index=f.findIndex(v=>pointKey(v)===pointKey(corner));
  assert(index>=0);assert.equal(dot(vsub(f[(index+1)%4],corner),vsub(f[(index+3)%4],corner)).sign(),expected,'Dot corner angles must agree with the source figure');
 }
 for(let a=0;a<3;a++){
  const lo=tile.faceDots[2*a],hi=tile.faceDots[2*a+1];
  const fixed=tile.kind==='prolate'?'blackCorner':'redCorner',opposite=tile.kind==='prolate'?'redCorner':'blackCorner';
  assert.equal(pointKey(vadd(lo[fixed],tile.edges[a])),pointKey(hi[fixed]));
  assert.equal(pointKey(tile.edges.reduce(vadd,vector(0n,0n,0n))),pointKey(vadd(lo[opposite],hi[opposite])));
  const copy=translatedDecoration(tile,tile.edges[a]);assert.equal(prepare(tile).faces[2*a+1],prepare(copy).faces[2*a]);
  assert(compatiblePair(tile,copy));for(const variant of decorateGeometry(copy.geometry))assert(!pointMarkingsAgree(tile,variant),'No decoration variant may allow the simple periodic parallelotope copy');
 }
 // Reflection exchanges the two hands. Mirror x exactly and recover the
 // transformed inventory member by its face-center component assignments.
 const mirror=p=>vector(p[0].neg(),p[1],p[2]);
 const mapping=[{axis:0,sign:1},{axis:1,sign:1},{axis:3,sign:1},{axis:2,sign:1},{axis:5,sign:-1},{axis:4,sign:-1}];
 const target=tile.axes.map(a=>mapping[a]);let origin=vector(0n,0n,0n);for(const t of target)if(t.sign<0)origin=vsub(origin,STAR[t.axis]);
 const geom=makeRhombohedron(target.map(t=>t.axis),origin);
 const wanted=tile.faceDots.map(f=>[pointKey(mirror(f.center)),pointKey(mirror(f.blackCorner)),pointKey(mirror(f.redCorner))].join('/')).sort().join('|');
 const recovered=decorateGeometry(geom).find(t=>t.faceDots.map(f=>[pointKey(f.center),pointKey(f.blackCorner),pointKey(f.redCorner)].join('/')).sort().join('|')===wanted);
 assert(recovered);assert.notEqual(recovered.decoration.hand,tile.decoration.hand);
}
// An independently constructed patch must admit the supplied face rules.
// This witness is used for verification only; the live engine never imports it.
const patch=makeIcosahedralPatch({radius:1}),domains=patch.tiles.map(decorateGeometry),owner=new Map(),contacts=[];
for(let i=0;i<domains.length;i++)for(let f=0;f<6;f++){const k=pointKey(domains[i][0].pointMarkings[f].point);if(owner.has(k)){const[j,g]=owner.get(k);contacts.push([i,f,j,g]);}else owner.set(k,[i,f]);}
const sig=(t,f)=>JSON.stringify(t.pointMarkings[f].components);let trials=0;
function solve(ds){trials++;let change=true;while(change){change=false;for(const[a,f,b,g]of contacts){const sa=new Set(ds[a].map(t=>sig(t,f))),sb=new Set(ds[b].map(t=>sig(t,g))),aa=ds[a].filter(t=>sb.has(sig(t,f))),bb=ds[b].filter(t=>sa.has(sig(t,g)));if(!aa.length||!bb.length)return null;if(aa.length!==ds[a].length){ds[a]=aa;change=true;}if(bb.length!==ds[b].length){ds[b]=bb;change=true;}}}const i=ds.findIndex(d=>d.length>1);if(i<0)return ds;assert(trials<10000);for(const t of ds[i]){const next=ds.slice();next[i]=[t];const r=solve(next);if(r)return r;}return null;}
assert(solve(domains),'Published face patterns must decorate the independent 540-tile witness');
const s=new FaceSearch({markings:'ammann',seed:4,target:60,budget:500});
const before=s.inspect(),checkpoint=s.trail.length,t=[...s.candidates.values()].find(r=>r.legal).tile;
s.apply(t);assert(s.pointMarkings.inspect().values.some(([,channels])=>channels.some(([, ,refs])=>refs===2)));s.undo(checkpoint);assert.deepEqual(s.inspect(),before);
function oracle(){const placed=[...s.placed.values()].map(r=>r.tile);for(const p of s.frontier.values()){
 const expected=faceAttachments(p.owner.tile,p.owner.faceIndex).flatMap(decorateGeometry).filter(c=>!s.candidates.get(c.id)?.excluded&&!s.placed.has(c.id)&&placed.every(t=>compatiblePair(c,t)&&pointMarkingsAgree(c,t))).map(c=>c.id).sort();
 assert.deepEqual([...p.candidates].sort(),expected,'Incremental graph must match exhaustive geometry-plus-point-marking replay');
}}
for(let i=0;i<8;i++){oracle();s.step();}
while(!['checkpoint','budget','exhausted'].includes(s.state))s.step();assert.equal(s.state,'checkpoint');assert.equal(s.placed.size,60);assert.equal(s.summary().dead,0);assert(s.stats.eliminatedMarking>0);assert(s.stats.backtracks>0);oracle();
const placed=[...s.placed.values()].map(r=>r.tile);for(let i=0;i<placed.length;i++)for(let j=i+1;j<placed.length;j++){assert(compatiblePair(placed[i],placed[j]));assert(pointMarkingsAgree(placed[i],placed[j]));}
const json=JSON.parse(JSON.stringify(s.export(),(_,v)=>typeof v==='bigint'?String(v):v));assert.equal(json.markings.source,'supplied');assert.equal(json.markings.learned,false);assert.equal(json.windowFilter,false);assert.equal(json.tiles.length,60);
console.log(`ok: 120 decorated orientations / 4 chiral prototypes; exact source-angle and opposite-face rules; mirror action; periodic-copy rejection; 540-tile independent witness; marked graph oracle; full m-state rollback; 60-tile search with ${s.stats.backtracks} backtracks and ${s.stats.eliminatedMarking} incremental marking removals`);
