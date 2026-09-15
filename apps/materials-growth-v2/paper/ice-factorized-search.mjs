import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeFactorizedCloudSearch} from './factorized-cloud-search.mjs';
import {cloudContains} from './portable-cloud-filter.mjs';
const [sourcePath,blocksPath,dest]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const source=JSON.parse(readFileSync(sourcePath)),data=JSON.parse(readFileSync(blocksPath));
assert.equal(data.sourceModelHash,hash(sourcePath));
const sourceHashes=Object.fromEntries(['ice-factorized-search.mjs','factorized-cloud-search.mjs','factorized-point-search.mjs','factorized-point-state.mjs','factorized-candidate-domain.mjs','portable-cloud-filter.mjs'].map(n=>[n,hash(new URL(n,import.meta.url))]));
// Recompute endpoint domains without enumerating the Cartesian product. This
// audit uses the shared numerical predicate, not an independent cloud verifier.
function audit(e){
 const totals=new Map([...e.points.keys()].map(p=>[p,0])),owners=new Set();
 for(const id of e.placed.keys()){
  const {block:b}=e.decode(id);assert(!owners.has(b.inventory));owners.add(b.inventory);
  for(const t of b.t)totals.set(t.point,totals.get(t.point)+t.value);
 }
 for(const [id,p] of e.points){assert.equal(p.total,totals.get(id));assert(p.total<=e.capacity);assert.equal(e.graph.has(id),p.active&&p.total<e.capacity);}
 for(const b of e.blocks){
  const enabled=!owners.has(b.inventory)&&b.t.every(t=>totals.get(t.point)+t.value<=e.capacity);
  const allowed=b.endpointChoices.map((choices,side)=>choices.map((c,i)=>e.points.get(b.markPoints[side]).marks.every(a=>cloudContains(source.clouds[c.cloud],source.clouds[a.value.cloud],2*e.modelRadius+1e-10)!==null)?i:null).filter(i=>i!==null));
  assert.equal(b.domain.count,enabled?BigInt(allowed[0].length)*BigInt(allowed[1].length):0n);
  for(let side=0;side<2;side++)assert.deepEqual([...b.domain.endpointIndices(side)],allowed[side]);
  for(const [point,indices] of e.graph)assert.equal(indices.has(b.index),b.domain.count>0n&&b.t.some(t=>t.point===point));
 }
}
// Incidence-set insertion order is not used by candidateIds (numeric sorting).
// As in the reference semanticState, compare graph membership canonically.
// Frontier order affects only the reported dead/unknown point, not the action:
// advance backtracks on any dead point and stops on any unknown point. It does
// not use those diagnostic point identities in pruning or branch iteration.
const snapshot=e=>JSON.stringify({points:[...e.points],graph:[...e.graph].map(([p,v])=>[p,[...v].sort((a,b)=>a-b)]).sort(([a],[b])=>a.localeCompare(b)),domains:e.blocks.map(b=>b.domain.snapshot()),owners:[...e.owners],placed:[...e.placed]},(_,v)=>typeof v==='bigint'?v.toString():v);
mkdirSync(dest);const results=[];
for(const row of data.models){
 const setup=performance.now(),e=makeFactorizedCloudSearch(row,source.clouds);e.modelRadius=row.cloudRadius;
 audit(e);const root=snapshot(e),setupSeconds=(performance.now()-setup)/1000;
 const start=performance.now();let steps=0,last;
 while(steps<1000000&&performance.now()-start<30000){last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;}
 const seconds=(performance.now()-start)/1000;const auditStart=performance.now();audit(e);
 const marking=e.cloudCheck(),selected=[...e.placed.keys()].map(id=>{const {index,left,right,block}=e.decode(id);return {id,index,block:block.id,left,right};});
 const scalarComplete=[...e.points.values()].every(p=>!p.active||p.total===e.capacity);
 const result={file:row.file,fold:row.fold,setupSeconds,seconds,steps,stats:{...e.stats},cloudStats:{...e.cloudStats},selected:selected.length,scalarComplete,markingStatus:marking.status,commonValues:marking.witnesses.length,status:scalarComplete&&marking.valid?'complete-awaiting-independent-verification':last?.kind==='exhausted'?'exhausted-finite-pool':last?.kind==='unknown'?'unknown-common-value':'budget-unknown'};
 e.undo(0);audit(e);
 if(snapshot(e)!==root){
  const before=JSON.parse(root),after=JSON.parse(snapshot(e));
  const differences=Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])).map(key=>({key,before:before[key],after:after[key]}));
  writeFileSync(`${dest}/${row.fold}-rollback-failure.json`,JSON.stringify({sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),sourceHashes,result,differences}),{flag:'wx'});
  throw Error('Root rollback mismatch; see saved diagnostic. Run is not certified.');
 }
 result.rootRollback=true;result.finalAuditSeconds=(performance.now()-auditStart)/1000;
 writeFileSync(`${dest}/${row.fold}.json`,JSON.stringify({sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),sourceHashes,result,selected,commonWitnesses:marking.witnesses}),{flag:'wx'});
 results.push(result);console.log(JSON.stringify(result));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Full Cartesian endpoint markings in a finite registered ice pool; global dead/forced/earliest-generation search. Thirty-second search budget per frame; setup and final audits separate. No training selection supplied to search.',sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),sourceHashes,results,limits:'Shared numerical cloud predicates in runtime audits. Independent witness replay pending. No continuous-pose completeness, negative specificity, condition-matched provenance or blind growth claim.'},null,2),{flag:'wx'});
