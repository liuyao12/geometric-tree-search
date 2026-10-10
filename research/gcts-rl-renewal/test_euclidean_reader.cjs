'use strict';
const fs=require('fs'),assert=require('assert'),path=require('path');
const base=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const reader=require(path.join(base,'euclidean-proofs.js'));
const d=JSON.parse(fs.readFileSync(path.join(base,'euclidean-reader-001.json')));
let mutations=0,cells=0;
for(const p of d.proofs){
 assert(reader.validateGeometryRow(p));cells+=p.length;
 assert(reader.geometryFormula(p.target).includes('\\forall'));
 for(let i=0;i<p.length;i++){
  const q=structuredClone(p);q.tiles[i].marks[0][1]+=1;
  assert.throws(()=>reader.validateGeometryRow(q));mutations++;
  const r=structuredClone(p);r.tiles[i].formula_id+=1;
  assert.throws(()=>reader.validateGeometryRow(r));mutations++;
 }
 const rotated=structuredClone(p);rotated.tiles[0].weights[0][0]=[1,1];
 assert.throws(()=>reader.validateGeometryRow(rotated));mutations++;
}
console.log(JSON.stringify({proofs:d.proofs.length,cells,mutationRejections:mutations}));
