'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const reader=require('../../docs/research/gcts-rl-renewal/hilbert-proofs.js');
const file=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal/hilbert-reader-001.json');
const data=JSON.parse(fs.readFileSync(file));let rejected=0,cells=0;
assert.equal(data.audit.status,'passed');
for(const p of data.proofs){
 assert(reader.validateHilbertRow(p));
 for(let i=0;i<p.length;i++){
  cells++;
  for(const change of [q=>q.tiles[i].weights[0][1]=11,q=>q.tiles[i].marks[0][1]++,q=>q.tiles[i].formula_id++,q=>q.tiles[i].slot++,q=>q.tiles[i].root_line=-1,q=>q.tiles[i].formula=['bot']]){
   const q=structuredClone(p);change(q);assert.throws(()=>reader.validateHilbertRow(q));rejected++;
  }
  for(const a of [p.tiles[i].formula,p.tiles[i].formula[2]]){
   assert(reader.hilbertFormula(a).length>0);assert(reader.hilbertEnglish(a).length>0);
  }
 }
 for(const change of [q=>q.tiles.pop(),q=>q.native.status='unknown_step_budget',q=>q.target=['bot'],q=>q.tiles.at(-1).refs[0]=q.length]){
  const q=structuredClone(p);change(q);assert.throws(()=>reader.validateHilbertRow(q));rejected++;
 }
 for(const l of p.primitive){assert(reader.hilbertFormula(l.formula));assert(reader.hilbertEnglish(l.formula));}
 assert(reader.hilbertFormula(p.theory.axioms['I.1-existence']).includes('\\exists'));
 assert(reader.hilbertFormula(p.theory.axioms['I.3-plane-points']).includes('\\exists'));
}
assert.equal(data.proofs.length,2);assert.equal(cells,6);
console.log(JSON.stringify({proofs:data.proofs.length,cells,mutations_rejected:rejected,primitive_lines:data.proofs.reduce((n,p)=>n+p.primitive_lines,0)}));
