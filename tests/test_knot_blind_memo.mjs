import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {extensionComponents} from '../research/knot-classifier/local-extension-markings.mjs';
import {latticeProvider} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
const records=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url))).records;
const sample=[records[1],records[14],records[35],records[84],records[249],records[801],records.at(-1)];
let domains=0,edges=0;
for(const r of sample){
 const cache=new Map(),fresh=latticeMoves(r.vertices,{maxEdges:240}).map(m=>m.key).sort();
 for(let repetition=0;repetition<2;repetition++){
  const provider=latticeProvider(r.vertices,r.vertices,{maxEdges:240,model:new LocalPointMarkings({enabled:false}),authorDomainCache:cache});
  const domain=provider.domain(provider.sourceKey),found=domain.candidates.map(e=>provider.resolve(e)?.key).filter(Boolean).sort();
  assert.equal(domain.complete,true);assert.deepEqual(found,fresh);domains++;edges+=found.length;
 }
 const components=extensionComponents(r.vertices,sample[0].vertices);
 const translated=r.vertices.map(p=>p.map((x,i)=>x+[7,-13,4][i]));
 assert.deepEqual(extensionComponents(translated,sample[0].vertices.map(p=>p.map((x,i)=>x+[7,-13,4][i]))).map(c=>[c.signature,c.masks]),components.map(c=>[c.signature,c.masks]));
}
console.log(JSON.stringify({passed:true,domains,edges,completeMemoizedInventory:true,translationPreserved:true}));
