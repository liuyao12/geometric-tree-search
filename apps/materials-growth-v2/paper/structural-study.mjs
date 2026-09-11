// Fixed descriptive validation matrix; never changes production search rules.
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {samplePatch} from '../samples.mjs';
import {discover,learnSections} from '../learning.mjs';
import {MaterialExperiment} from '../material.mjs';
import {compose,inverse} from '../geometry.mjs';
import {scoreStructure} from './structural-metrics.mjs';
const drain=g=>{let r;do{r=g.next();}while(!r.done);return r.value;};
const milestones=[64,128,220];
if(!isMainThread){
  const {id,epsilon,observedOnly}=workerData,start=performance.now();
  const sample=samplePatch(id),grammar=drain(discover(sample.atoms,{epsilon}));
  const e=new MaterialExperiment(grammar,drain(learnSections(grammar,{observedOnly})),{maximumPoints:80000,maximumCandidates:160000});
  const prepared=performance.now();
  for(let step=1;step<=220;step++){
    const event=e.step();
    if(['unknown','budget','exhausted','complete'].includes(event.kind)){parentPort.postMessage({kind:'terminal',step,event,elapsedMs:performance.now()-start});break;}
    if(milestones.includes(step)){
      const state=e.snapshot(false),first=e.engine.candidates.get(e.engine.placed.keys().next().value);
      const poses=grammar.types[first.meta.type].occurrences.map(o=>compose(o.pose,inverse(first.meta.pose)));
      const metrics=sample.evaluation?scoreStructure(sample.evaluation,state.atoms,{poses,epsilon}):null;
      parentPort.postMessage({kind:'checkpoint',step,metrics,types:grammar.types.length,trainingAtoms:sample.atoms.length,stats:{...e.engine.stats},legal:state.validation.legal,overlapLegal:state.overlapValidation?.legal??null,preparationMs:prepared-start,elapsedMs:performance.now()-start,atoms:state.atoms});
    }
  }
}else{
  const cases=['ice','copper'].flatMap(id=>(id==='ice'?[.015,.03,.06]:[.03]).flatMap(epsilon=>[false,true].map(observedOnly=>({id,epsilon,observedOnly}))));
  const report={schema:'gcts-structural-validation/1',created:new Date().toISOString(),protocol:{cases,milestones,hardTimeoutSeconds:120,maximumPoints:80000,maximumCandidates:160000,scope:'Eight deterministic sensitivity runs, not independent material replicates. No held-out training test. Fixed seed-centred spherical windows at 2,4,6 times the shortest reference separation. Same global alignment as first-placement witnesses. Structural metrics are evaluation-only; no chemistry supplied to search. Time includes checkpoint evaluation and is not a performance benchmark.'},sources:{},results:[]};
  const files=['kernel.mjs','material.mjs','learning.mjs','geometry.mjs','overlap-rules.mjs','samples.mjs','paper/structural-study.mjs','paper/structural-metrics.mjs'];
  for(const p of files)report.sources[p]=createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex');
  const save=()=>{if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');};save();
  for(const c of cases){
    const row={...c,checkpoints:[],status:'running'};report.results.push(row);save();
    await new Promise(resolve=>{
      const w=new Worker(new URL(import.meta.url),{workerData:c});
      const timer=setTimeout(async()=>{row.status='timeout';await w.terminate();save();resolve();},120000);
      w.on('message',m=>{if(m.kind==='checkpoint'){row.checkpoints.push(m);console.log(JSON.stringify({...c,step:m.step,precision:m.metrics?.sitePrecision,recall:m.metrics?.windows.map(w=>w.siteRecall),compositionTV:m.metrics?.compositionTV}));}else{row.terminal=m;row.status=m.event.kind;}save();});
      w.once('error',e=>{row.status='error';row.error=e.message;clearTimeout(timer);save();resolve();});
      w.once('exit',code=>{clearTimeout(timer);if(row.status==='running')row.status=code===0?'finished':'worker-error';save();resolve();});
    });
  }
  console.log('Completed structural validation matrix.');
}
