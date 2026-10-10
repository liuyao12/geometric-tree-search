'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const docs=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal'),file=path.join(docs,'induction-clusters-view-001.json'),raw=fs.readFileSync(file),data=JSON.parse(raw);
const {readClusterProof}=require(path.join(docs,'induction-cluster-reading.js'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let cells=0,atomicTiles=0,metatiles=0,classicalProposals=0,mutationRejections=0;
function reject(record,change){const changed=structuredClone(record);change(changed);assert.throws(()=>readClusterProof(changed));mutationRejections++;}
for(const p of data.proofs){
 const steps=readClusterProof(p);cells+=steps.length;atomicTiles+=p.atomic_tiles.length;metatiles+=p.atomic_tiles.filter(t=>t.item).length;classicalProposals+=p.classical_proposals.length;
 assert.equal(steps.length,p.problem.length);assert.deepEqual(steps.at(-1).formula,p.problem.target);
 const certificate=fs.readFileSync(path.join(docs,p.certificate_file));assert.equal(sha(certificate),p.certificate_sha256);assert.deepEqual(JSON.parse(certificate),p.request);
 reject(p,r=>{r.tiles[0].marks.find(([point])=>point[1]===1&&point[0]===2*r.tiles[0].slot)[1]=-1;});
 reject(p,r=>{r.tiles[0].weights[0][1]=6;});
 reject(p,r=>{const t=r.tiles.find(t=>t.refs.length);t.refs[0]=t.slot;});
 reject(p,r=>{r.problem.theory.schemas=[];});
 reject(p,r=>{r.initial_marks.find(([point])=>point[1]===4)[1]=1;});
 reject(p,r=>{const t=r.tiles.find(t=>t.reason.kind==='block'),line=r.request.proof[t.root_line];line.name='missing-definition';});
 if(p.atomic_tiles.length){
  reject(p,r=>{r.atomic_tiles[0].weights[0][1]=6;});
  reject(p,r=>{r.atomic_tiles[0].marks.find(([point])=>point[1]===2)[1]=-1;});
  reject(p,r=>{r.tiles[0].parent_candidate=-1;});
 }else{
  reject(p,r=>{r.classical_proposals.push({members:[[r.tiles[0].slot,-1,[]]]});});
 }
}
const ledger={proofRecords:data.proofs.length,cells,atomicTiles,metatiles,classicalProposals,mutationRejections,view_sha256:sha(raw),sources:Object.fromEntries(['induction-tile-reading.js','induction-cluster-reading.js'].map(n=>[n,sha(fs.readFileSync(path.join(docs,n)))])),runner_sha256:sha(fs.readFileSync(__filename)),scope:'Every readable cell validates its actual primitive inference and root certificate. Every selected GCTS atomic tile equals its constituent capacity/marking union; fixed target/resource boundary values agree globally. Classical proposal members bind the final assignment and have no atomic chronology. Mutations cover output ports, capacity, premises, induction authorization, boundary, block interface, atomic point data, ownership and fabricated classical proposals.'};
fs.writeFileSync(path.join(docs,'induction-cluster-reading-tests-001.json'),JSON.stringify(ledger)+'\n');console.log(JSON.stringify(ledger));
