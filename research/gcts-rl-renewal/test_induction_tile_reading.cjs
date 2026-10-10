'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const docs=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const source=path.join(docs,'induction-tile-reading.js');
const {readInductionTiles}=require(source),raw=fs.readFileSync(path.join(docs,'induction-proofs-view-001.json')),data=JSON.parse(raw);
let cells=0,rewrites=0,joins=0,rejections=0;
for(const proof of data.proofs){
 const steps=readInductionTiles(proof);cells+=steps.length;rewrites+=steps.filter(s=>s.change).length;joins+=steps.filter(s=>s.kind==='induction').length;
 assert(steps.some(s=>s.kind==='conditional-reflexivity'));assert(steps.some(s=>s.kind==='generalize'));assert.equal(steps.filter(s=>s.kind==='induction').length,1);
 const mutate=fn=>{const bad=JSON.parse(JSON.stringify(proof));fn(bad);assert.throws(()=>readInductionTiles(bad));rejections++;};
 mutate(p=>{p.tiles[0].weights[0][1]=6;});
 mutate(p=>{p.tiles[0].marks.find(([q])=>q[1]===1&&q[0]===2*p.tiles[0].slot)[1]++;});
 mutate(p=>{p.tiles.pop();});
 mutate(p=>{const t=p.tiles.find(t=>t.refs.length);t.refs[0]=t.slot;});
 mutate(p=>{const t=p.tiles.find(t=>t.refs.length);t.input_ids[0]++;});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.operation==='conditional-rewrite');t.reason.context.hypothesis=['eq',['fun','zero',[]],['fun','zero',[]]];});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.axiom==='fixed-induction-hypothesis');t.reason.move.bindings.n=['fun','zero',[]];});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.operation==='rewrite');t.reason.move.path=[99];});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.operation==='rewrite');t.reason.move.direction=0;});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.witness?.rule==='generalize');t.reason.witness.variable='wrong';});
 mutate(p=>{p.tiles.find(t=>t.reason.operation==='induction').reason.variable='wrong';});
 mutate(p=>{p.problem.theory.schemas=[];});
 mutate(p=>{const t=p.tiles.find(t=>t.reason.kind==='block'),l=p.request.proof[t.root_line];p.request.blocks.find(b=>b.name===l.name).premises.push(['bot']);});
}
assert.equal(data.proofs.filter(p=>p.lane!=='csp').length,2);assert.equal(data.proofs.filter(p=>p.lane==='csp').length,1);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const result={proofs:data.proofs.length,cells,axiomOrHypothesisRewrites:rewrites,inductionJoins:joins,mutationRejections:rejections,
 source_sha256:sha(fs.readFileSync(source)),test_sha256:sha(fs.readFileSync(__filename)),view_sha256:sha(raw),scope:'Decode the actual searched induction cells, bind all output/premise ports and checked root/block interfaces, validate every fixed-hypothesis/axiom rewrite and induction/generalization shape; reject altered markings, metadata, references, occupancy and schema authorization. Natural-language style is not a separate logical certificate.'};
fs.writeFileSync(path.join(docs,'induction-tile-reading-tests-001.json'),JSON.stringify(result)+'\n');console.log(JSON.stringify(result));
