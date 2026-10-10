'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const docs=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const {readWangTiles}=require(path.join(docs,'wang-tile-reading.js'));
const tiles=JSON.parse(fs.readFileSync(path.join(docs,'wang-tiles-001.json'))),proofs=JSON.parse(fs.readFileSync(path.join(docs,'wang-proofs-001.json')));
let cells=0,rewrites=0,clusters=0;
for(const row of tiles.theorems){
 const proof=proofs.theorems.find(t=>t.id===row.id),read=readWangTiles(row,proof);
 assert.equal(read.steps.length,row.length);assert.equal(read.chain.length,row.length);
 assert.deepEqual(read.conclusion,row.formulas[row.target_id]);
 assert.deepEqual(read.groups.flatMap(g=>g.cells),read.chain.map(s=>s.slot));
 for(const step of read.steps){cells++;if(step.kind==='rewrite'){rewrites++;assert.deepEqual(step.premise_formula,row.formulas[row.tiles.flatMap(t=>t.outputs).find(o=>o.slot===step.references[0]).formula_id]);}}
 clusters+=read.groups.filter(g=>g.kind==='searched cluster').length;
 const wrongMark=structuredClone(row);wrongMark.tiles[0].marks.find(([p])=>p[1]===1)[1]=-1;
 assert.throws(()=>readWangTiles(wrongMark,proof),/point values/);
 const wrongReason=structuredClone(row);wrongReason.tiles.flatMap(t=>t.outputs).find(o=>o.references.length).label='missing-axiom';
 assert.throws(()=>readWangTiles(wrongReason,proof),/Missing equality axiom/);
 const wrongTarget=structuredClone(row);wrongTarget.target_id=-1;
 assert.throws(()=>readWangTiles(wrongTarget,proof),/target port mismatch/);
 const wrongAxiom=structuredClone(proof);wrongAxiom.theory.axioms.AS=['eq',['fun','zero',[]],['fun','zero',[]]];
 assert.throws(()=>readWangTiles(row,wrongAxiom),/not an instance/);
 const wrongPremise=structuredClone(row),rewriter=wrongPremise.tiles.find(t=>t.outputs.some(o=>o.references.length));
 const source=rewriter.outputs.find(o=>o.references.length).references[0];rewriter.marks.find(([p])=>p[0]===2*source&&p[1]===1)[1]=-1;
 assert.throws(()=>readWangTiles(wrongPremise,proof),/Premise port|point values/);
}
const donor=tiles.theorems.find(t=>t.id==='donor-2');assert.deepEqual(donor.tiles.map(t=>t.members[0][0]),[0,1,3,2]);assert.deepEqual(readWangTiles(donor,proofs.theorems.find(t=>t.id===donor.id)).chain.map(s=>s.slot),[0,1,2,3]);
console.log(JSON.stringify({theorems:tiles.theorems.length,cells,axiomMatchedRewrites:rewrites,searchedClusters:clusters,mutationRejections:50,logicalOrderDistinctFromPlacementOrder:true}));
