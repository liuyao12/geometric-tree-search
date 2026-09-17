// Publish a compact, hash-linked record without redistributing coordinates.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [proposalPath,poolPath,searchPath,checkPath,out]=process.argv.slice(2);
const read=p=>JSON.parse(readFileSync(p));
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const [proposal,pool,search,check]=[proposalPath,poolPath,searchPath,checkPath].map(read);
assert(proposal.noFixed&&pool.noFixed&&!pool.usedSuppliedPoses);
assert.equal(search.poolHash,sha(poolPath));
assert.equal(check.poolHash,sha(poolPath));
assert.equal(check.repairHash,sha(searchPath));
const ids=rows=>rows.map(r=>r.id).sort();
assert.deepEqual(ids(proposal.rows),ids(pool.models));
assert.deepEqual(ids(search.results),ids(pool.models));
assert.deepEqual(ids(check.rows),ids(pool.models));
assert.equal(new Set(ids(pool.models)).size,pool.models.length);
const rows=pool.models.map(model=>{
 const p=proposal.rows.find(r=>r.id===model.id),s=search.results.find(r=>r.id===model.id),c=check.rows.find(r=>r.id===model.id);
 assert.equal(model.model.initial.length,0);assert.equal(s.fixed,0);
 assert.equal(s.complete,c.complete);assert(s.rollbackVerified);
 assert.equal(p.candidateCount,model.model.candidates.length);
 const parent=new Map(s.selected.map(id=>[id,id]));
 const find=id=>parent.get(id)===id?id:find(parent.get(id));
 const atomOwner=new Map();
 for(const id of s.selected)for(const atom of model.geometry[id].ids){
  if(atomOwner.has(atom))parent.set(find(id),find(atomOwner.get(atom)));
  else atomOwner.set(atom,id);
 }
 const components=new Map();
 for(const id of s.selected){const root=find(id);components.set(root,(components.get(root)??0)+1);}
 return {id:model.id,atoms:c.atoms,candidates:p.candidateCount,correspondenceLeaves:p.correspondenceLeaves,proposalTruncated:p.truncated,
  proposalAndDiagnosticSeconds:p.seconds,status:s.status,complete:c.complete,placements:c.placements,
  fullyFilled:c.fullyFilled,partiallyFilled:c.partiallyFilled,untouched:c.untouched,
  maxPositionErrorAngstrom:c.maxPositionErrorAngstrom,duplicateTypeCorrespondences:c.duplicateTypeCorrespondences,
  supportComponents:components.size,componentPlacementCounts:[...components.values()].sort((a,b)=>b-a),
  selectedMotifTypes:new Set(s.selected.map(id=>model.geometry[id].type)).size,
  searchSeconds:s.seconds,stats:s.stats,rollbackVerified:s.rollbackVerified};
});
const report={sourceHashes:pool.sourceHashes,proposalHash:sha(proposalPath),poolHash:sha(poolPath),searchHash:sha(searchPath),checkHash:sha(checkPath),
 summarizerHash:sha(new URL(import.meta.url)),generatorHash:pool.codeHash,kernelHash:search.kernelHash,
 initialization:search.initialization,budget:search.budget,rows,
 completeConfigurations:rows.filter(r=>r.complete).length,totalConfigurations:rows.length,
 limits:'Frozen support library; supplied motif types and training poses upstream. No supplied selected placements or pose list used by candidate generation in this lane. Known target atoms and opaque species remain inputs. All finite-pool roots generation zero. No m-values. Untruncated means this bounded registration pass finished, not continuous-pose completeness. Upstream dictionary saw calibration frames. Support components count shared target atoms, not physical bonds or spatial connectivity. Not independent-condition validation, single-atom growth, or growth beyond the sample.'};
writeFileSync(out,JSON.stringify(report,null,2),{flag:'wx'});
console.log(JSON.stringify(report,null,2));
