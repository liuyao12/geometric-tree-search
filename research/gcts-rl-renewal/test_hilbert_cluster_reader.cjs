'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const reader=require('../../docs/research/gcts-rl-renewal/hilbert-clusters.js');
const docs=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const data=JSON.parse(fs.readFileSync(path.join(docs,'hilbert-cluster-reader-001.json')));let rejected=0,cells=0,clusters=0;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(data.audit.status,'passed');assert.equal(data.results.length,28);assert.equal(data.proofs.length,3);assert.equal(data.library.length,16);
assert.equal(sha(fs.readFileSync(path.join(docs,data.source.file))),data.source.sha256);
assert.equal(sha(fs.readFileSync(path.join(docs,data.arithmetic.file))),data.arithmetic.sha256);
for(const p of data.proofs){
 assert(reader.validateClusterRow(p,data.library));
 const mutate=change=>{const q=structuredClone(p);change(q);assert.throws(()=>reader.validateClusterRow(q,data.library));rejected++;};
 for(let i=0;i<p.length;i++){
  cells++;
  for(const change of [q=>q.tiles[i].weights[0][1]=11,q=>q.tiles[i].marks[0][1]++,q=>q.tiles[i].formula_id++,q=>q.tiles[i].slot++,q=>q.tiles[i].root_line=-1,q=>q.tiles[i].formula=['bot'],q=>q.tiles[i].candidate++,q=>q.tiles[i].rule_id++])mutate(change);
  assert(reader.hilbertFormula(p.tiles[i].formula));assert(reader.hilbertEnglish(p.tiles[i].formula));
 }
 for(let i=0;i<p.groups.length;i++){
  for(const change of [q=>q.groups[i].weights[0][1]=11,q=>q.groups[i].marks[0][1]++,q=>q.groups[i].members[0][0]++,q=>q.groups[i].candidate++,q=>q.groups[i].incoming.push([99,0]),q=>q.groups[i].outgoing.push([99,0])])mutate(change);
  if(p.groups[i].item){clusters++;mutate(q=>q.groups[i].item.start++);mutate(q=>q.groups[i].item.patterns[0]='absent-family');}
 }
 for(const change of [q=>q.tiles.pop(),q=>q.groups.pop(),q=>q.native.status='unknown_step_budget',q=>q.target=['bot'],q=>q.primitive.at(-1).formula=['bot'],q=>q.tiles.at(-1).refs[0]=q.length])mutate(change);
 for(const l of p.primitive){assert(reader.hilbertFormula(l.formula));assert(reader.hilbertEnglish(l.formula));}
}
assert.equal(cells,29);assert(clusters>=3);
for(const name of ['unique-joining-line','joining-exists-reordered']){
 const runs=data.results.filter(r=>r.id===name);assert.equal(runs.length,8);
 for(const replica of [0,1])assert.equal(runs.filter(r=>r.replica===replica).length,4);
}
assert(data.results.filter(r=>r.id==='unique-joining-line'&&r.lane==='gcts-base').every(r=>r.status==='unknown_search_budget'));
assert(data.results.filter(r=>r.id==='unique-joining-line'&&r.lane==='gcts-motifs').every(r=>r.states===19&&r.status==='finite_exact_proof_tiling'));
assert(data.results.filter(r=>r.id==='joining-exists-reordered'&&r.lane==='gcts-base').every(r=>r.states===901));
assert(data.results.filter(r=>r.id==='joining-exists-reordered'&&r.lane==='gcts-motifs').every(r=>r.states===195));
assert(data.results.filter(r=>r.id.startsWith('joining-no-')||r.id==='joining-short').every(r=>r.status==='exhausted_finite_proof_envelope'));
console.log(JSON.stringify({proofs:data.proofs.length,cells,selected_clusters:clusters,mutations_rejected:rejected,primitive_lines:data.proofs.reduce((n,p)=>n+p.primitive_lines,0),evaluation_records:data.results.length}));
