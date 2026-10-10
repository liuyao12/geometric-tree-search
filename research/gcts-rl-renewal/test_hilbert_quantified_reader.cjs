'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const reader=require('../../docs/research/gcts-rl-renewal/hilbert-quantified.js');
const data=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../docs/research/gcts-rl-renewal/hilbert-quantified-reader-001.json')));let rejected=0,cells=0,binders=0;
assert.equal(data.audit.status,'passed');
assert.notEqual(reader.hilbertFormula(['var','fresh0']),reader.hilbertFormula(['var','fresh1']));
for(const p of data.proofs){
 assert(reader.validateHilbertRow(p));
 for(let i=0;i<p.length;i++){
  cells++;binders+=Number(p.tiles[i].formula[0]==='all');
  for(const change of [q=>q.tiles[i].weights[0][1]=11,q=>q.tiles[i].marks[0][1]++,q=>q.tiles[i].formula_id++,q=>q.tiles[i].slot++,q=>q.tiles[i].root_line=-1,q=>q.tiles[i].formula=['bot']]){
   const q=structuredClone(p);change(q);assert.throws(()=>reader.validateHilbertRow(q));rejected++;
  }
  assert(reader.hilbertFormula(p.tiles[i].formula));assert(reader.hilbertEnglish(p.tiles[i].formula));
 }
 for(const change of [q=>q.tiles.pop(),q=>q.native.status='unknown_step_budget',q=>q.target=['bot'],q=>q.tiles.at(-1).refs[0]=q.length]){
  const q=structuredClone(p);change(q);assert.throws(()=>reader.validateHilbertRow(q));rejected++;
 }
 for(const l of p.primitive){assert(reader.hilbertFormula(l.formula));assert(reader.hilbertEnglish(l.formula));}
}
assert.equal(data.proofs.length,2);assert.equal(cells,22);assert.equal(binders,4);
assert.equal(data.proofs[0].lane,'gcts');assert.equal(data.proofs[1].lane,'csp');
console.log(JSON.stringify({proofs:data.proofs.length,cells,generalization_cells:binders,mutations_rejected:rejected,primitive_lines:data.proofs.reduce((n,p)=>n+p.primitive_lines,0)}));
