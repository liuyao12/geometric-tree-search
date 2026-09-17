import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [poolPath,kernelPath,out]=process.argv.slice(2),pool=JSON.parse(readFileSync(poolPath));
const maxSteps=Number(process.argv[5]??100000),maxMilliseconds=Number(process.argv[6]??10000);
assert(Number.isSafeInteger(maxSteps)&&maxSteps>0);
assert(Number.isFinite(maxMilliseconds)&&maxMilliseconds>0);
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const {PointSearch,verify}=await import(pathToFileURL(kernelPath)),results=[];
for(const row of pool.models){
 const start=performance.now(),e=new PointSearch(row.model),root=JSON.stringify(e.semanticState());let last,steps=0;
 while(steps<maxSteps&&performance.now()-start<maxMilliseconds){last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;}
 const selected=[...e.placed.keys()],check=verify(row.model,selected);assert(check.legal);e.auditGraph();
 if(last?.kind==='complete')assert(check.complete);
 const result={id:row.id,status:last?.kind??'budget-unknown',complete:check.complete,selected,steps,stats:{...e.stats},seconds:(performance.now()-start)/1000,
               fixed:row.model.initial.length,selectedAdded:selected.filter(id=>!id.startsWith('fixed:')).length};
 if(!['complete','exhausted','unknown'].includes(result.status))result.status='budget-unknown';
 e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);result.rollbackVerified=true;results.push(result);console.log(JSON.stringify({...result,selected:undefined}));
}
writeFileSync(out,JSON.stringify({poolHash:sha(poolPath),kernelHash:sha(kernelPath),runnerHash:sha(new URL(import.meta.url)),results,
 budget:{maxSteps,maxMilliseconds},
 initialization:pool.models.every(r=>r.model.initial.length===0)?'empty-placement-state':'supplied-fixed-prefixes',
 limits:'Reference unmarked finite point search on supplied target atoms and finite geometry proposals. Prefix counts explicitly reported. No feasibility-solver selection used. Not single-atom unbounded growth, not complete continuous poses, not learned marking acceleration.'},null,2),{flag:'wx'});
