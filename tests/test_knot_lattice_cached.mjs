import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
import {solveLatticeIterative,latticeProvider} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url)));
const cache=new Map();let inventories=0;
for(const c of corpus.records.filter(c=>c.crossings>=3&&c.crossings<=8)){
 const plain=latticeMoves(c.vertices,{maxEdges:240}),memo=latticeMoves(c.vertices,{maxEdges:240,diagramMoveCache:cache});
 assert.deepEqual(memo.map(m=>[m.key,m.kind]).sort(),plain.map(m=>[m.key,m.kind]).sort());inventories++;
}
for(const id of ['3_1','8_1']){
 const p=corpus.records.find(r=>r.id===id).vertices;
 for(const v of [[...p].reverse(),[...p.slice(2),...p.slice(0,2)]])assert.deepEqual(latticeMoves(v,{maxEdges:240,diagramMoveCache:cache}).map(m=>[m.key,m.kind]).sort(),latticeMoves(v,{maxEdges:240}).map(m=>[m.key,m.kind]).sort());
}
const p=corpus.records.find(r=>r.id==='3_1').vertices,q=latticeMoves(p)[0].vertices;
const model=new LocalExtensionMarkings();model.compile(p,q,1);
assert.ok(Object.isSealed(model));assert.throws(()=>Object.defineProperty(model,'version',{value:999}),TypeError);
assert.throws(()=>Object.setPrototypeOf(model.events,{}),/Immutable/);
class Unsupported extends LocalExtensionMarkings{}
assert.throws(()=>latticeProvider(p,q,{extensionModel:new Unsupported()}),/native immutable/);
const before=model.activationValidationNodes;model.validateTransfer();model.validateTransfer();assert.equal(model.activationValidationNodes,before);assert.equal(model.transferValidationNodes,0);
const marked=solveLatticeIterative(p,q,{maxDepth:3,maxMs:10000,nodeCap:1000,extensionModel:model});
const plain=solveLatticeIterative(p,q,{maxDepth:3,maxMs:10000,nodeCap:1000,learn:false,extensionLearn:false});
assert.equal(marked.knotEquivalence,'equivalent');assert.equal(plain.knotEquivalence,'equivalent');
assert.equal(marked.certificate.steps.length,1);assert.equal(plain.certificate.steps.length,1);
assert.deepEqual(marked.attempts.map(a=>a.depth),[0,1]);assert.deepEqual(plain.attempts.map(a=>a.depth),[0,1]);
assert.equal(marked.stats.nodes,marked.attempts.reduce((n,a)=>n+a.stats.nodes,0));
const budget=solveLatticeIterative(p,q,{maxDepth:3,maxMs:0});assert.equal(budget.knotEquivalence,'unknown');assert.equal(budget.attempts.length,0);
console.log(JSON.stringify({passed:true,inventories,diagrams:cache.size,cachedTransferNodes:model.transferValidationNodes,iterativeCertificateMoves:marked.certificate.steps.length}));
