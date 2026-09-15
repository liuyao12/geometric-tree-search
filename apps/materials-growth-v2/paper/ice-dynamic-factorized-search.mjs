import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeFactorizedCloudSearch} from './factorized-cloud-search.mjs';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
import {SupportOrderedFactorizedSearch} from './support-ordered-factorized-search.mjs';
import {InterleavedFactorizedSearch} from './interleaved-factorized-search.mjs';
import {CoupledEndpointSearch} from './coupled-endpoint-search.mjs';
import {RelationalEndpointSearch} from './relational-endpoint-search.mjs';
const [sourcePath,blocksPath,dest,indexPath,indexCheckPath,ordering='baseline',relationPath,relationCheckPath]=process.argv.slice(2),hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
assert(['baseline','support-rich','interleaved','coupled-observed','context-relation'].includes(ordering));
const source=JSON.parse(readFileSync(sourcePath)),data=JSON.parse(readFileSync(blocksPath));assert.equal(data.sourceModelHash,hash(sourcePath));
const relation=ordering==='context-relation'?JSON.parse(readFileSync(relationPath)):null;
if(relation){const check=JSON.parse(readFileSync(relationCheckPath));assert.equal(check.relationHash,hash(relationPath));assert.equal(relation.libraryHash,source.portableHash);}
const index=indexPath?JSON.parse(readFileSync(indexPath)):null;
if(index){const check=JSON.parse(readFileSync(indexCheckPath));assert.equal(index.blocksHash,hash(blocksPath));assert.equal(index.sourceModelHash,hash(sourcePath));assert.equal(check.indexHash,hash(indexPath));assert.equal(check.blocksHash,hash(blocksPath));}
const sourceHashes=Object.fromEntries(['ice-dynamic-factorized-search.mjs','dynamic-factorized-support.mjs','factorized-cloud-search.mjs','factorized-point-state.mjs','factorized-point-search.mjs','factorized-candidate-domain.mjs','portable-cloud-filter.mjs'].map(n=>[n,hash(new URL(n,import.meta.url))]));
if(index){sourceHashes.partnerIndex=hash(indexPath);sourceHashes.partnerIndexCheck=hash(indexCheckPath);}
sourceHashes.supportOrdering=hash(new URL('support-ordered-factorized-search.mjs',import.meta.url));
sourceHashes.interleavedOrdering=hash(new URL('interleaved-factorized-search.mjs',import.meta.url));
if(ordering==='coupled-observed')sourceHashes.coupledModel=hash(new URL('coupled-endpoint-search.mjs',import.meta.url));
if(relation){sourceHashes.relationModel=hash(new URL('relational-endpoint-search.mjs',import.meta.url));sourceHashes.relation=hash(relationPath);sourceHashes.relationCheck=hash(relationCheckPath);}
const snapshot=e=>JSON.stringify({points:[...e.points],graph:[...e.graph].map(([p,v])=>[p,[...v].sort()]).sort(),domains:e.blocks.map(b=>b.domain.snapshot()),owners:[...e.owners],placed:[...e.placed]});
mkdirSync(dest);const results=[];
for(const [rowIndex,row] of data.models.entries()){
 const partnerIndex=index?.models[rowIndex]??null;if(partnerIndex){assert.equal(partnerIndex.file,row.file);assert.equal(partnerIndex.fold,row.fold);}
 const setup=performance.now();
 const model=relation?{...row,allowedPairs:row.blocks.map(b=>b.endpointChoices[0].flatMap((c,i)=>{const allowed=new Set(relation.neighbors[c.sourceMotif]);return b.endpointChoices[1].flatMap((d,j)=>allowed.has(d.sourceMotif)?[[i,j]]:[]);} ))}:row;
 const e=makeFactorizedCloudSearch(model,source.clouds,{Engine:relation?RelationalEndpointSearch:ordering==='coupled-observed'?CoupledEndpointSearch:ordering==='interleaved'?InterleavedFactorizedSearch:ordering==='support-rich'?SupportOrderedFactorizedSearch:DynamicFactorizedSupportSearch,partnerIndex});
 const root=snapshot(e),setupSeconds=(performance.now()-setup)/1000;console.log(JSON.stringify({phase:'setup',file:row.file,seconds:setupSeconds,supportStats:e.supportStats}));
 const start=performance.now();let steps=0,last,lastProgress=start;
 while(steps<1000000&&performance.now()-start<30000){
  last=e.advance();steps++;
  if(performance.now()-lastProgress>10000){console.log(JSON.stringify({phase:'search',file:row.file,steps,selected:e.placed.size,seconds:(performance.now()-start)/1000}));lastProgress=performance.now();}
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 const seconds=(performance.now()-start)/1000,marking=e.cloudCheck();
 const selected=[...e.placed.keys()].map(id=>{const {index,left,right,block}=e.decode(id);return {id,index,left,right,block:block.id};});
 const scalarComplete=[...e.points.values()].every(p=>!p.active||p.total===2);
 const result={file:row.file,fold:row.fold,setupSeconds,seconds,steps,selected:selected.length,scalarComplete,markingStatus:marking.status,commonValues:marking.witnesses.length,stats:{...e.stats},supportStats:{...e.supportStats},cloudStats:{...e.cloudStats},status:scalarComplete&&marking.valid?'complete-awaiting-independent-verification':last?.kind==='exhausted'?'exhausted-finite-pool':last?.kind==='unknown'?'unknown-common-value':'budget-unknown'};
 result.ordering=ordering;
 if(ordering==='coupled-observed')result.modelRestriction='Only endpoint pairs with equal sourceCandidate identity; learned restricted hypothesis, not redundant factorized pruning.';
 if(relation)result.modelRestriction='Frozen training-calibrated endpoint substitution relation; learned restricted hypothesis, not redundant factorized pruning. Overlap marking radius unchanged.';
 const undoStart=performance.now();e.undo(0);assert.equal(snapshot(e),root);result.rootRollback=true;result.undoSeconds=(performance.now()-undoStart)/1000;
 writeFileSync(`${dest}/${row.fold}.json`,JSON.stringify({sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),indexHash:indexPath?hash(indexPath):null,indexCheckHash:indexCheckPath?hash(indexCheckPath):null,sourceHashes,result,selected,commonWitnesses:marking.witnesses}),{flag:'wx'});results.push(result);console.log(JSON.stringify(result));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Dynamic complementary support to a fixed point after every change, then unchanged global dead/forced/earliest-generation DFS. Every surviving decorated candidate remains distinct.',sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),sourceHashes,preprocessing:data.supportPreprocessing,results,limits:'Correctness-first global recomputation, not incremental support maintenance. Thirty-second search budget checked between atomic advances; one advance may overshoot. Setup and rollback separate. Scalar exhaustive domain tests; independent material witness replay required. No full continuous-pose or blind-growth claim.'},null,2),{flag:'wx'});
