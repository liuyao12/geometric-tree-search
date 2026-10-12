import {readFileSync,writeFileSync,appendFileSync,mkdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {solveLatticeIterative} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
const args=process.argv.slice(2),get=(k,d)=>args.find(a=>a.startsWith(`--${k}=`))?.slice(k.length+3)??d;
const directory=get('directory','/private/tmp/knot-escalation'),worker=get('lane',null);mkdirSync(directory,{recursive:true});
if(worker){
 const m=JSON.parse(readFileSync(`${directory}/manifest.json`)),marked=worker==='extension-transfer',model=marked?new LocalPointMarkings():null,extensionModel=marked?new LocalExtensionMarkings({probeNodeCap:m.bounds.extensionProbeNodeCap}):null;
 const file=`${directory}/${worker}.jsonl`;writeFileSync(file,'');
 for(const [caseIndex,c]of m.cases.entries()){
  const initialVersion=extensionModel?.version;
  const result=solveLatticeIterative(c.source,c.target,{...m.bounds,learn:marked,extensionLearn:marked,model,extensionModel});
  const run={caseIndex,initialVersion,...result,maxRSSKiB:process.resourceUsage().maxRSS};appendFileSync(file,JSON.stringify(run)+'\n');
  console.log(JSON.stringify({lane:worker,knot:c.evaluatorKnot,seedPair:c.seedPair,status:run.status,moves:run.certificate?.steps.length,nodes:run.stats.nodes,totalMs:run.totalMs,reason:run.reason,horizons:run.attempts.map(a=>[a.depth,a.status,a.stats?.nodes]),transferMs:run.extensions?.transferValidationMsThisRun}));
 }
 writeFileSync(`${directory}/${worker}-runtime.json`,JSON.stringify({node:process.version,maxRSSKiB:process.resourceUsage().maxRSS}));
}else{
 const previous=JSON.parse(readFileSync('research/knot-classifier/lattice-through8-benchmark.json'));
 const selected=get('knots','3_1,4_1,5_1,6_1,7_1,8_1').split(',');
 const retry=get('retry-report',null),retryData=retry?JSON.parse(readFileSync(retry)):null;
 const retryKeys=retryData?new Set(retryData.lanes.find(l=>l.lane==='extension-transfer').runs.filter(r=>!r.certificate).map(r=>{const c=retryData.cases[r.caseIndex];return `${c.evaluatorKnot}:${c.seedPair}`;})):null;
 const cases=previous.cases.filter(c=>retryKeys?retryKeys.has(`${c.evaluatorKnot}:${c.seedPair}`):selected.includes(c.evaluatorKnot));
 const bounds={...previous.bounds,maxMs:Number(get('max-ms',60000)),nodeCap:Number(get('node-cap',5000)),stateCap:200000};
 const manifest={version:'lattice-immutable-iterative-escalation-v1',previousBenchmark:'lattice-through8-benchmark.json',stepsPerIndependentScramble:5,region:null,cases,bounds,preparationMs:0,inputGenerationCostPreviouslyReportedMs:previous.preparationMs,selection:retry?'All remaining marked unknowns from the paired previous stage, with matched retry budgets in both lanes and all earlier costs retained.':'First prime reference type at each crossing count from three through eight; all three original seed pairs, with no replacement or new scrambling. Representative larger-budget experiment, not all 35 types at this budget.',scope:'Query-local exact diagram endpoint-map memoization in both lanes. Increasing finite horizons zero through ten, same neutral bidirectional search and aggregate bounds. Sequential fresh workers; one initially empty immutable native proof catalog reused across all marked queries. New proof alphabet, resolved labels and stencil validated once before freezing; transfer uses constant-time native gate. No archived learned assignments imported. All lattice face locations available; unchanged restricted fixed-projection move grammar.'};
 if(retry)manifest.previousStage=retry;
 writeFileSync(`${directory}/manifest.json`,JSON.stringify(manifest));const started=performance.now(),lanes=[];
 for(const lane of get('lanes','extension-transfer,unmarked').split(',')){
  const child=spawnSync(process.execPath,[fileURLToPath(import.meta.url),`--directory=${directory}`,`--lane=${lane}`],{stdio:'inherit'});if(child.status!==0)throw Error(`Worker failed: ${lane}`);
  lanes.push({lane,runs:readFileSync(`${directory}/${lane}.jsonl`,'utf8').trim().split('\n').map(JSON.parse),runtime:JSON.parse(readFileSync(`${directory}/${lane}-runtime.json`))});
 }
 const report={...manifest,incomplete:false,lanes,experimentMs:performance.now()-started};
 writeFileSync(get('output','research/knot-classifier/lattice-escalation-benchmark.json'),JSON.stringify(report)+'\n');
 console.log(JSON.stringify({summary:lanes.map(l=>({lane:l.lane,success:l.runs.filter(r=>r.certificate).length,unknown:l.runs.filter(r=>!r.certificate).length,totalMs:l.runs.reduce((n,r)=>n+r.totalMs,0)}))}));
}
