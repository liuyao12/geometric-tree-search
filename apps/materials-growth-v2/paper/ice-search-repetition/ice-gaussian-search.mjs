import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {gaussianPointClass} from './gaussian-point-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {capacityLookaheadClass} from './point-capacity-lookahead.mjs';
const args=process.argv.slice(2),lookahead=args[0]==='--lookahead';if(lookahead)args.shift();
const [input,kernel,dest]=args,data=JSON.parse(readFileSync(input));
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const {PointSearch,verify}=await import(pathToFileURL(kernel));mkdirSync(dest);const results=[];
for(const row of data.models)for(const enabled of [false,true]){
 const model=row.model,Gaussian=gaussianPointClass(linearFrontierClass(PointSearch),model,{enabled}),Engine=lookahead?capacityLookaheadClass(Gaussian,model):Gaussian;
 const setup=performance.now(),e=new Engine(model),setupSeconds=(performance.now()-setup)/1000,root=JSON.stringify(e.semanticState());
 const start=performance.now();let last,steps=0;
 while(performance.now()-start<30000&&steps<100000){last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;}
 const seconds=(performance.now()-start)/1000,selected=[...e.placed.keys()],basic=verify(model,selected);assert(basic.legal);e.auditGraph();
 const result={id:row.id,enabled,lookahead,setupSeconds,seconds,steps,stats:{...e.stats},fieldStats:{...e.fieldStats},capacityStats:e.capacityStats?{...e.capacityStats}:null,status:last?.kind==='complete'?'complete-awaiting-independent-replay':last?.kind==='exhausted'?'exhausted-finite-pool':'unknown',selected,scalarComplete:basic.complete};
 e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);assert.equal(e.fieldOwners.size,0);assert.equal(e.fieldAssignments.size,0);result.rootRollback=true;
 writeFileSync(`${dest}/${row.id}-${enabled}.json`,JSON.stringify(result,null,2),{flag:'wx'});results.push(result);console.log(JSON.stringify({...result,selected:selected.length}));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({inputScope:data.scope,inputLimits:data.limits,sourceHash:hash(input),kernelHash:hash(kernel),codeHashes:Object.fromEntries(['ice-gaussian-search.mjs','gaussian-point-filter.mjs','linear-frontier-decision.mjs','point-capacity-lookahead.mjs'].map(f=>[f,hash(new URL(f,import.meta.url))])),results,limits:'Finite registered point-search control; see input scope for supplied geometry. Optional lookahead is proved redundant t-capacity filtering, not learned GCTS. Thirty-second cooperative search budget; a single update may exceed it. Preprocessing, setup and audit not included. Radius developmental; independent field replay pending.'},null,2),{flag:'wx'});
