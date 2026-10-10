'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),R=require('../../docs/research/gcts-rl-renewal/movable-regions.js');
const doc=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const v=JSON.parse(fs.readFileSync(path.join(doc,'movable-regions-reader-001.json')));
assert.equal(R.validate(v).proofs,18);
let pointMutations=0,sourceMutations=0,structuralMutations=0,primitiveMutations=0,erased=0;
function reject(f){assert.throws(f);}
for(const c of v.cases)for(const lane of ['baseline','marked']){
 const r=c.runs[lane];if(!('proof' in r))continue;
 for(const tile of r.tiles)for(const entry of tile.marks){const old=entry[1];entry[1]='wrong';reject(()=>R.points(c,r,lane));entry[1]=old;pointMutations++;}
 for(const row of r.proof){const old=row.formula;row.formula=['bot'];reject(()=>R.P.checkRows(r.proof,c.spec.target,c.spec.hypotheses,c.spec.theory,v.family));row.formula=old;sourceMutations++;}
 let old=r.endpoint;r.endpoint++;reject(()=>R.points(c,r,lane));r.endpoint=old;structuralMutations++;
 old=r.tiles[0].occupancy[0][1];r.tiles[0].occupancy[0][1]=11;reject(()=>R.points(c,r,lane));r.tiles[0].occupancy[0][1]=old;structuralMutations++;
 old=r.closing_cluster.occupancy[0][1];r.closing_cluster.occupancy[0][1]=11;reject(()=>R.cluster(c,r,lane));r.closing_cluster.occupancy[0][1]=old;structuralMutations++;
 if(lane==='marked'){const a=JSON.parse(JSON.stringify(r));for(const t of a.tiles)t.marks=t.marks.filter(([p])=>p[0]!==-2000);a.closing_cluster.marks=a.closing_cluster.marks.filter(([p])=>p[0]!==-2000);R.points(c,a,'baseline');R.cluster(c,a,'baseline');erased++;}
 for(const request of [r.compiled_request,r.deduced_request].filter(Boolean)){
  for(const lines of request.blocks.map(b=>b.proof).concat([request.proof])){
   const selected=lines.map((a,i)=>i===0||i===lines.length-1||['generalize','instantiate','distribute'].includes(a.rule)?i:-1).filter(i=>i>=0);
   for(const i of selected){old=lines[i].formula;lines[i].formula=['bot'];reject(()=>R.P.checkRequest(request));lines[i].formula=old;primitiveMutations++;}
  }
 }
}
let metadataMutations=0;
for(const c of v.cases)for(const p of c.learned_points){const old=p.assignments[0].value;p.assignments[0].value=1;reject(()=>R.validate(v));p.assignments[0].value=old;metadataMutations++;}
for(const cached of v.cache.cases){const old=cached.request.target;cached.request.target=['bot'];reject(()=>R.validate(v));cached.request.target=old;metadataMutations++;}
assert.equal(R.validate(v).proofs,18);
console.log(JSON.stringify({proofs:18,point_mutations_rejected:pointMutations,source_mutations_rejected:sourceMutations,structural_mutations_rejected:structuralMutations,primitive_mutations_rejected:primitiveMutations,projection_mutations_rejected:metadataMutations,erased_positive_proofs:erased}));
