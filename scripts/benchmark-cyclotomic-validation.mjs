import {performance} from 'node:perf_hooks';
import {writeFileSync} from 'node:fs';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {knownPenroseBenchmark} from './penrose-known-benchmark.mjs';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
const trainSeeds=[1,17],testSeeds=[5,11,23,47],targetCount=30,nodeLimit=10000;
const repetitions=Number(process.env.REPEATS||3),certificates=[],training=[],results=[];
function run(seed,mode){
 const start=performance.now(),problem=blindPenroseProblem();
 const adapter=mode==='known'?knownPenroseBenchmark(problem):{problem};
 const search=createObstructionSearch({...adapter,seed,targetCount,nodeLimit,learn:mode==='cold'||mode==='frozen',train:mode==='cold',initialCertificates:mode==='frozen'?certificates:[]});
 while(!search.next().done){}
 const s=search.snapshot(),ms=performance.now()-start;
 if(s.status!=='target reached')throw Error(`${mode}/${seed}: ${s.status}`);
 return{seed,mode,ms,proposals:s.stats.proposals,backtracks:s.stats.backtracks,baseChecks:s.stats.baseChecks,corona:s.minimumFrontierGeneration,rules:s.learning?.rules||0,entries:s.learning?.entries||0,certificates:s.learning?.certificates||[]};
}
for(const seed of trainSeeds){const r=run(seed,'cold');certificates.push(...r.certificates);training.push({...r,certificates:undefined});console.log('training',JSON.stringify(training.at(-1)));}
// Rotate lane order, rebuilding every problem; never share candidate caches.
const modes=['plain','frozen','known'];
for(let repeat=0;repeat<repetitions;repeat++)for(let i=0;i<testSeeds.length;i++)for(let j=0;j<modes.length;j++){
 const mode=modes[(repeat+i+j)%modes.length],r=run(testSeeds[i],mode);
 const result={...r,repeat,certificates:undefined};results.push(result);console.log(JSON.stringify(result));
}
const totals=Object.fromEntries(modes.map(mode=>[mode,results.filter(r=>r.mode===mode).reduce((s,r)=>s+r.ms,0)]));
const trainingMs=training.reduce((s,r)=>s+r.ms,0),savingPerRun=(totals.plain-totals.frozen)/(testSeeds.length*repetitions);
const summary={trainingMs,totals,frozenSpeedup:totals.plain/totals.frozen,estimatedBreakEvenRuns:savingPerRun>0?Math.ceil(trainingMs/savingPerRun):null};
const report={trainSeeds,testSeeds,targetCount,nodeLimit,repetitions,training,results,summary,certificates};
writeFileSync(process.env.OUTPUT||'/tmp/cyclotomic-validation.json',JSON.stringify(report,null,2)+'\n');console.log('summary',JSON.stringify(summary));
