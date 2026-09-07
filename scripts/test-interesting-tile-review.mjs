import assert from 'node:assert/strict';
import {INTERESTING_TILE_REVIEW as review, tileSpecs, isGctsFigureVisibleInCatalog} from '../apps/3d-lattice-tiler/engine.js';
const perms=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
const vertices=cell=>{const v=[...cell.base], out=[[...v]];for(const axis of cell.order){v[axis]++;out.push([...v]);}return out;};
const key=verts=>verts.map(v=>v.join(',')).sort().join(';');
const patterns=new Map(perms.map((order,i)=>[key(vertices({base:[0,0,0],order})),i]));
for(const c of review.candidates) {
 const system=tileSpecs.TILING_REGISTRY[c.registry_id];assert.ok(system);assert.ok(system.build()[0]);
 const figure=tileSpecs.figureCatalog.find(f=>f.census_candidate?.id===c.id);assert.ok(figure);assert.ok(isGctsFigureVisibleInCatalog(figure));
 assert.equal(c.screening.status,'other_model_research');assert.ok(c.research_review.note.includes('weighted'));
 if(c.research_review.classification!=='periodic')continue;
 const cert=c.research_review.certificate.geometric_periodic;
 const {hnf,placements}=cert.witness;
 const [a,b,cc,d,e,f]=hnf, seen=new Set();
 for(const p of placements)for(const cell of c.alcoves) {
  const vv=vertices(cell).map(v=>p.permutation.map((axis,i)=>p.sign*v[axis]+p.translation[i]));
  const base=[0,1,2].map(i=>Math.min(...vv.map(v=>v[i])));
  const orientation=patterns.get(key(vv.map(v=>v.map((x,i)=>x-base[i]))));assert.notEqual(orientation,undefined);
  let [x,y,z]=base;let q=Math.floor(z/f);x-=q*cc;y-=q*e;z-=q*f;q=Math.floor(y/d);x-=q*b;y-=q*d;x-=Math.floor(x/a)*a;
  const k=[x,y,z,orientation].join(',');assert.ok(!seen.has(k),'overlapping quotient alcoves');seen.add(k);
 }
 assert.equal(seen.size,6*a*d*f);assert.equal(placements.length,24);
}
console.log('Three research tiles registered; two 24-copy geometric certificates independently replayed; model scope kept separate.');
