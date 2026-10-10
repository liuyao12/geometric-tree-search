'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const doc=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal'),V=require(path.join(doc,'quantified-receptors.js')),data=JSON.parse(fs.readFileSync(path.join(doc,'quantified-receptors-reader-001.json')));assert.equal(V.validate(data),true);
let marks=0,rows=0,primitive=0,native=0;
for(const c of data.cases){if(!c.runs.gcts.proof)continue;
 for(let t=0;t<c.runs.gcts.tiles.length;t++)for(let m=0;m<c.runs.gcts.tiles[t].marks.length;m++){const b=structuredClone(c);b.runs.gcts.tiles[t].marks[m][1]='?';assert.throws(()=>V.points(b));marks++;}
 for(let i=0;i<c.runs.gcts.proof.length;i++){const b=structuredClone(c.runs.gcts.proof);b[i].formula=['bot'];assert.throws(()=>V.checkRows(b,c.spec.target,c.spec.hypotheses,c.spec.theory,data.family));rows++;}
 for(const request of [c.compiled_request,c.deduced_request].filter(Boolean)){
  const scopes=request.blocks.map(b=>({proof:b.proof,target:b.conclusion,premises:b.premises})).concat([{proof:request.proof,target:request.target,premises:[]}]);
  for(const s of scopes){const sample=new Set([0,s.proof.length-1,...s.proof.map((r,j)=>['generalize','distribute','instantiate'].includes(r.rule)?j:-1).filter(j=>j>=0)]);for(const j of sample){const b=structuredClone(s.proof);b[j].formula=['bot'];assert.throws(()=>V.primitive(b,s.target,s.premises,request.theory));primitive++;}}
 }
}
const keys=['target','theory','assumptions','forbidden','registry','proved','pending'];
for(let ci=0;ci<data.native.cases.length;ci++){const n=data.native.cases[ci];for(let j=0;j<n.lines.length;j++)for(const direction of ['input','output']){
 const b=structuredClone(data),key=keys[j%keys.length];b.native.cases[ci].lines[j][direction][key]=key==='target'?['bot']:key==='theory'?{}:['changed'];assert.throws(()=>V.validate(b));native++;
}for(const j of [0,n.lines.length-1])for(const key of keys){const b=structuredClone(data);b.native.cases[ci].lines[j].input[key]=key==='target'?['bot']:key==='theory'?{}:['changed'];assert.throws(()=>V.validate(b));native++;}}
const a=['pred','A',[]],b=['pred','B',[]],theory={functions:{},predicates:{A:0,B:0},axioms:{},schemas:[]};const invalid=['imp',['or',a,a],b];assert.throws(()=>V.primitive([{rule:'tautology',formula:invalid}],invalid,[],theory));const good=['imp',a,['imp',b,a]];assert.equal(V.primitive([{rule:'tautology',formula:good}],good,[],theory),true);
const p=['pred','P',[['var','x']]],scopeTheory={functions:{},predicates:{P:1},axioms:{},schemas:[]};assert.throws(()=>V.primitive([{rule:'assumption',formula:p,index:0},{rule:'generalize',formula:['all','x',p],variable:'x',source:0}],['all','x',p],[p],scopeTheory));
console.log(JSON.stringify({proofs:10,native_commands:42,point_mutations_rejected:marks,source_mutations_rejected:rows,primitive_mutations_rejected:primitive,native_context_mutations_rejected:native,tautology_and_scope_regressions:3}));
