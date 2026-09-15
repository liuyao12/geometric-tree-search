// Diagnose the first failed child without changing the search or pruning it.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeFactorizedCloudSearch} from './factorized-cloud-search.mjs';
const [sourcePath,blocksPath,output]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const source=JSON.parse(readFileSync(sourcePath)),data=JSON.parse(readFileSync(blocksPath));
assert.equal(data.sourceModelHash,hash(sourcePath));
const results=[];
for(const row of data.models){
 const e=makeFactorizedCloudSearch(row,source.clouds);let steps=0,last;
 while(steps<1000&&e.decision().kind!=='dead'){
  last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 const d=e.decision(),result={file:row.file,fold:row.fold,steps,decision:d,cylinders:[]};
 if(d.kind==='dead'){
  const selected=[...e.placed.keys()],id=selected.at(-1),choice=e.decode(id),b=choice.block;
  assert.equal(last.id,id);const prefix=selected.slice(0,-1);
  const checkpoint=e.checkpoint();assert(checkpoint>0);e.undo(checkpoint-1);
  const parents=b.endpointChoices.map((_,side)=>[...b.domain.endpointIndices(side)]);
  assert(b.domain.enabled);e.apply(id);
  result.prefix=prefix;result.failed=id;
  // Fix t, inventory and one endpoint marking; erase the other endpoint.
  // Any dead point in this relaxed state certifies EVERY choice at the erased
  // endpoint impossible in this parent. A live relaxed state proves nothing.
  for(let erase=0;erase<2;erase++){
   const p=e.points.get(b.markPoints[erase]),saved=p.marks;
   p.marks=p.marks.filter(m=>m.owner!==id);e.refresh(new Set([p.id]));
   const relaxed=e.decision();
   result.cylinders.push({erase,keptSide:1-erase,keptIndex:erase===0?choice.right:choice.left,parentAlternatives:parents[erase].length,relaxedDecision:relaxed,certifiedDead:relaxed.kind==='dead'});
   p.marks=saved;e.refresh(new Set([p.id]));
  }
 }
 let records=0,unique=0,full=0n,deduplicated=0n;
 for(const b of row.blocks){const sizes=b.endpointChoices.map(cs=>{records+=cs.length;const n=new Set(cs.map(c=>JSON.stringify(source.clouds[c.cloud]))).size;unique+=n;return n;});full+=BigInt(b.endpointChoices[0].length)*BigInt(b.endpointChoices[1].length);deduplicated+=BigInt(sizes[0])*BigInt(sizes[1]);}
 result.identicalSerializedClouds={records,unique,conceptualCandidates:full.toString(),ifIdenticalValuesMerged:deduplicated.toString(),scope:'Diagnostic only; no candidate merging performed. Different point order may represent the same cloud.'};
 results.push(result);console.log(JSON.stringify({...result,prefix:result.prefix?.length}));
}
writeFileSync(output,JSON.stringify({sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),diagnosticHash:hash(new URL(import.meta.url)),results,limits:'First dead child per frame only. Erased-marking cylinders are parent-local necessary impossibility tests, not learned transferable markings. Independent certificate replay required; search is unchanged.'},null,2),{flag:'wx'});
