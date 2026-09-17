import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [baseSearchPath,baseCheckPath,prefix,out]=process.argv.slice(2);
const read=p=>JSON.parse(readFileSync(p)),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const base=read(baseSearchPath),baseCheck=read(baseCheckPath);
assert.equal(baseCheck.repairHash,sha(baseSearchPath));assert(baseCheck.rows.every(r=>r.complete));
const runs=[];
for(const channels of [1,2,4,8]){
 const poolPath=`${prefix}-${channels}-pool-v1.json`,searchPath=`${prefix}-${channels}-search-v1.json`,checkPath=`${prefix}-${channels}-check-v1.json`;
 const pool=read(poolPath),search=read(searchPath),check=read(checkPath);
 assert.equal(check.searchHash,sha(searchPath));assert.equal(check.poolHash,sha(poolPath));assert.equal(pool.sourcePoolHash,base.poolHash);
 assert.deepEqual(search.results.map(r=>r.id),base.results.map(r=>r.id));
 const rows=search.results.map((r,i)=>{
  const entry=pool.models[i],b=base.results[i];assert.equal(entry.id,r.id);
  const candidates=new Map(entry.model.candidates.map(c=>[c.id,c]));
  const bounds=new Map();
  for(const id of b.selected)for(const m of candidates.get(id).m){
   const key=JSON.stringify([m.point,m.channel]),v=bounds.get(key)??[-Infinity,Infinity];
   bounds.set(key,[Math.max(v[0],m.lo),Math.min(v[1],m.hi)]);
  }
  const conflicts=[...bounds.values()].filter(([lo,hi])=>lo>hi).length;
  const markedCheck=check.rows.find(x=>x.id===r.id);assert.equal(markedCheck.complete,r.complete);
  const parent=new Map(r.selected.map(id=>[id,id])),owner=new Map(),supports=new Map();
  const find=id=>parent.get(id)===id?id:find(parent.get(id));
  for(const id of r.selected){const g=entry.geometry[id];
   for(const atom of g.ids){if(owner.has(atom))parent.set(find(id),find(owner.get(atom)));else owner.set(atom,id);}
   const key=JSON.stringify([g.type,g.ids.map((a,j)=>[a,g.units[j]]).sort((a,b)=>a[0]-b[0])]);supports.set(key,(supports.get(key)??0)+1);
  }
  return {id:r.id,complete:r.complete,baseCoverRetained:conflicts===0,baseCoverConflictingPointChannels:conflicts,
   selectedPlacements:r.selected.length,newSelectedIds:r.selected.filter(id=>!b.selected.includes(id)).length,
   supportComponents:new Set(r.selected.map(find)).size,repeatedUnorderedTypeSupports:[...supports.values()].reduce((a,n)=>a+n-1,0),
   stats:r.stats,seconds:r.seconds,geometryComplete:check.geometryReplay.rows.find(x=>x.id===r.id).complete};
 });
 const sum=(rows,f)=>rows.reduce((a,r)=>a+f(r),0);
 runs.push({channels,poolHash:sha(poolPath),searchHash:sha(searchPath),checkHash:sha(checkPath),markingHash:pool.marking.hash,
  complete:rows.filter(r=>r.complete).length,baseCoversRetained:rows.filter(r=>r.baseCoverRetained).length,
  totals:{attempts:sum(rows,r=>r.stats.attempts),branches:sum(rows,r=>r.stats.branches),forced:sum(rows,r=>r.stats.forced),backtracks:sum(rows,r=>r.stats.backtracks),seconds:sum(rows,r=>r.seconds)},rows});
}
const report={baseSearchHash:sha(baseSearchPath),baseCheckHash:sha(baseCheckPath),summarizerHash:sha(new URL(import.meta.url)),
 baseTotals:Object.fromEntries(['attempts','branches','forced','backtracks'].map(k=>[k,base.results.reduce((a,r)=>a+r.stats[k],0)])),runs,
 limits:'Same finite geometry candidates/order, target atoms, kernel and declared search budgets. Markings are training-only learned hypotheses, not proved redundant. Base-cover retention tests the saved unmarked search cover, not all possible unmarked covers. Alternate covers need not recover the supplied decomposition; disconnected supports and repeated sampled supports persist. Timing runs overlap and are not a controlled performance comparison. No independent-condition generalization, new anchor/m-support learning or growth beyond targets.'};
writeFileSync(out,JSON.stringify(report,null,2),{flag:'wx'});
console.log(JSON.stringify({baseTotals:report.baseTotals,runs:runs.map(({rows,...r})=>r)},null,2));
