// A declared inventory ablation, NOT a continuous-pose symmetry certificate.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [input,out]=process.argv.slice(2);
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const pool=JSON.parse(readFileSync(input));
assert(pool.noFixed&&!pool.usedSuppliedPoses);
const report=[];
for(const row of pool.models){
 assert.equal(row.model.initial.length,0);
 const groups=new Map();
 for(const candidate of row.model.candidates){
  assert.equal(candidate.m.length,0,'Cannot quotient future marking actions by unmarked t data');
  const g=row.geometry[candidate.id];assert(g);
  const key=JSON.stringify([g.type,candidate.t.map(x=>[x.point,x.value]).sort((a,b)=>a[0].localeCompare(b[0]))]);
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push(candidate.id);
 }
 // Keep first in pre-existing deterministic order, without seeing a solution.
 const representatives=new Set([...groups.values()].map(ids=>ids[0]));
 report.push({id:row.id,before:row.model.candidates.length,after:representatives.size,
  groups:[...groups.values()].filter(ids=>ids.length>1)});
 row.model.candidates=row.model.candidates.filter(c=>representatives.has(c.id));
 row.geometry=Object.fromEntries(Object.entries(row.geometry).filter(([id])=>representatives.has(id)));
}
const result={...pool,sourcePoolHash:sha(input),quotientCodeHash:sha(new URL(import.meta.url)),inventoryAblation:report,
 scope:'Unmarked one-per-type/mapped-t-support inventory ablation. Candidate order and first representative inherited from source pool; no selected witness read. This restricts multiplicity and is not proved equivalent to the distinct continuous-pose inventory. Not valid for future extended markings or proof of motif symmetry.'};
writeFileSync(out,JSON.stringify(result),{flag:'wx'});
console.log(JSON.stringify(report.map(({groups,...r})=>({...r,repeatedGroups:groups.length}))));
