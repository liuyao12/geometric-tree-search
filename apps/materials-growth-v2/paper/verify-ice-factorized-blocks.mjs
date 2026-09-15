import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {readLargeJSON} from './large-json-input.mjs';
import {createHash} from 'node:crypto';
import {FactorizedCandidateDomain} from './factorized-candidate-domain.mjs';
const [sourcePath,blocksPath,output]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const source=readLargeJSON(sourcePath),data=readLargeJSON(blocksPath);
assert.equal(data.sourceModelHash,hash(sourcePath));assert.equal(data.models.length,source.models.length);
const results=[];
for(let i=0;i<data.models.length;i++){
 const input=source.models[i],row=data.models[i],original=new Map(input.model.candidates.map(c=>[c.id,c]));
 assert.equal(row.file,input.file);assert.deepEqual(row.required,input.model.required);assert.equal(row.capacity,input.model.capacity);assert.equal(row.cloudRadius,input.model.cloudRadius);
 const seen=[new Set(),new Set()],byBlock=new Map();let count=0n,diagonals=0;
 for(const block of row.blocks){
  assert(!byBlock.has(block.id));byBlock.set(block.id,block);assert.equal(block.id,block.inventory);
  const left=block.endpointChoices[0],right=block.endpointChoices[1];assert.equal(block.endpointChoices.length,2);assert.equal(left.length,right.length);
  const domain=new FactorizedCandidateDomain(left.length,right.length);assert.equal(domain.count.toString(),block.candidateCount);count+=domain.count;
  for(let side=0;side<2;side++)for(const choice of block.endpointChoices[side]){
   assert(!seen[side].has(choice.sourceCandidate));seen[side].add(choice.sourceCandidate);
   const c=original.get(choice.sourceCandidate);assert(c);assert.equal(c.base,block.inventory);assert.deepEqual(c.t,block.t);assert.deepEqual(c.m,[]);
   assert.equal(c.registration.motif,choice.sourceMotif);assert.deepEqual(c.registration.rotationRow,block.rotationRow);
   assert.equal(c.cloudM[side].point,block.markPoints[side]);assert.equal(c.cloudM[side].cloud,choice.cloud);
  }
  for(let j=0;j<left.length;j++){assert.equal(left[j].sourceCandidate,right[j].sourceCandidate);assert(domain.has(j,j));diagonals++;}
  const cp=domain.checkpoint();domain.setEnabled(false);assert.equal(domain.count,0n);domain.undo(cp);assert.equal(domain.count.toString(),block.candidateCount);
 }
 for(const seenSide of seen)assert.deepEqual([...seenSide].sort(),[...original.keys()].sort());
 assert.equal(row.trainingLifts.length,input.trainingLifts.length);
 for(let k=0;k<row.trainingLifts.length;k++){
  const lift=row.trainingLifts[k];assert.equal(lift.name,input.trainingLifts[k].name);
  const recovered=lift.selected.map(c=>{
   assert.equal(c.left,c.right);const b=byBlock.get(c.block);assert(b);return b.endpointChoices[0][c.left].sourceCandidate;
  });assert.deepEqual(recovered,input.trainingLifts[k].selected);
 }
 const summary=data.summary[i];assert.equal(summary.file,row.file);assert.equal(summary.factorizedCandidates,count.toString());
 assert.equal(summary.coupledCandidates,diagonals);assert.equal(summary.storedEndpointChoices,2*diagonals);assert.equal(summary.geometricBlocks,row.blocks.length);
 results.push({...summary,trainingLiftsPreserved:row.trainingLifts.length});
}
const report={scope:'Independent endpoint-record replay and exact Cartesian cardinalities; no material search performed.',sourceModelHash:hash(sourcePath),blocksHash:hash(blocksPath),
 verifierHash:hash(new URL(import.meta.url)),domainHash:hash(new URL('./factorized-candidate-domain.mjs',import.meta.url)),results,
 limits:'All coupled candidates embed as diagonal choices; off-diagonal choices define a broader factorized hypothesis. No false-positive rate, continuous-pose completeness, runtime inventory/cloud-constraint integration or speedup claim.'};
writeFileSync(output,JSON.stringify(report,null,2),{flag:'wx'});console.log(JSON.stringify(report));
