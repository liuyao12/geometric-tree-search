// Bounded production-engine audit. The new connection descriptor is NOT enabled
// here: this isolates the remaining gap between local transfer and bulk growth.
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {samplePatch} from '../samples.mjs';
import {discover,learnSections} from '../learning.mjs';
import {MaterialExperiment} from '../material.mjs';
const drain=g=>{let r;do{r=g.next();}while(!r.done);return r.value;};
if(!isMainThread){
  const start=performance.now(),{id,observedOnly}=workerData,sample=samplePatch(id);
  const grammar=drain(discover(sample.atoms,{epsilon:.03}));
  parentPort.postMessage({stage:'discovery',atoms:sample.atoms.length,types:grammar.types.length});
  const marking=drain(learnSections(grammar,{observedOnly}));
  const e=new MaterialExperiment(grammar,marking,{maximumPoints:80000,maximumCandidates:160000});
  for(let step=1;step<=24;step++){
    const event=e.step();
    if(step%6===0||['unknown','budget','exhausted','complete'].includes(event.kind)){
      const s=e.snapshot(false);
      parentPort.postMessage({stage:'growth',step,event,atoms:s.atoms.length,legal:s.validation.legal,overlapLegal:s.overlapValidation?.legal??null,stats:{...e.engine.stats},elapsedMs:performance.now()-start});
    }
    if(['unknown','budget','exhausted','complete'].includes(event.kind))break;
  }
}else{
  const rows=[];
  for(const id of ['cdyb','asi'])for(const observedOnly of [false,true]){
    const row={id,observedOnly,status:'running',events:[]};rows.push(row);
    await new Promise(resolve=>{
      const w=new Worker(new URL(import.meta.url),{workerData:{id,observedOnly}});
      const timer=setTimeout(async()=>{row.status='timeout';await w.terminate();resolve();},45000);
      w.on('message',m=>{row.events.push(m);console.log(JSON.stringify({id,observedOnly,...m}));});
      w.on('error',e=>{row.status='error';row.error=e.message;clearTimeout(timer);resolve();});
      w.on('exit',code=>{clearTimeout(timer);if(row.status==='running')row.status=code===0?'finished':'worker-error';resolve();});
    });
  }
  const files=['kernel.mjs','material.mjs','learning.mjs','geometry.mjs','overlap-rules.mjs','samples.mjs','asi-sample.mjs','paper/aperiodic-growth-audit.mjs'];
  const sources=Object.fromEntries(files.map(p=>[p,createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex')]));
  if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify({schema:'aperiodic-production-audit/1',protocol:'Four deterministic 24-advance runs, 45 seconds per run, epsilon .03 Å, occupancy supports retained in both modes; observedOnly toggles existing relational filter. New descriptor/compiled hypothesis not enabled. No physical quality or growth-speed claim.',sources,rows},null,2)+'\n');
}
