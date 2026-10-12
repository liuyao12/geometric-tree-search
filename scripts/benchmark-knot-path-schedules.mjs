import {readFileSync,writeFileSync,appendFileSync,mkdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {solveLatticeIterative} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
const args=process.argv.slice(2),get=(name,fallback)=>args.find(a=>a.startsWith(`--${name}=`))?.slice(name.length+3)??fallback;
const directory=get('directory','/private/tmp/knot-path-schedules');mkdirSync(directory,{recursive:true});
const worker=get('worker',null);
if(worker){
 const manifest=JSON.parse(readFileSync(`${directory}/manifest.json`)),lane=manifest.lanes.find(l=>l.id===worker);
 const model=lane.marked?new LocalPointMarkings():null,extensionModel=lane.marked?new LocalExtensionMarkings({probeNodeCap:512}):null;
 const file=`${directory}/${worker}.jsonl`;writeFileSync(file,'');
 for(const [caseIndex,c]of manifest.cases.entries()){
  const initialVersion=extensionModel?.version;
  const run={caseIndex,initialVersion,...solveLatticeIterative(c.source,c.target,{...manifest.bounds,pathSchedule:lane.schedule,learn:lane.marked,extensionLearn:lane.marked,model,extensionModel}),maxRSSKiB:process.resourceUsage().maxRSS};
  appendFileSync(file,JSON.stringify(run)+'\n');
  console.log(JSON.stringify({lane:worker,knot:c.evaluatorKnot,seedPair:c.seedPair,status:run.status,moves:run.certificate?.steps.length,nodes:run.stats.nodes,totalMs:run.totalMs,reason:run.reason}));
 }
}else{
 const prior=JSON.parse(readFileSync('research/knot-classifier/lattice-escalation-benchmark.json'));
 const cases=prior.cases.filter(c=>c.evaluatorKnot==='3_1'&&c.seedPair===0||c.evaluatorKnot==='8_1'&&c.seedPair===1);
 const lanes=[{id:'balanced-gcts',schedule:'balanced',marked:true},{id:'adaptive-gcts',schedule:'smaller-frontier',marked:true},{id:'balanced-brute',schedule:'balanced',marked:false},{id:'adaptive-brute',schedule:'smaller-frontier',marked:false}];
 const manifest={version:'lattice-path-scheduler-comparison-v1',region:null,incomplete:true,bounds:{...prior.bounds,maxMs:Number(get('max-ms',120000))},cases,lanes,selection:'Two fixed existing pairs: trefoil seed 0 and the previously 60-second-unknown eight-crossing seed 1. No rescrambling, discarded case, injected path or imported model.',scope:'Matched fresh sequential workers. Both marked workers start empty and retain proofs across the same two knot types. All incident lattice faces, identical exact move grammar, point marking channels, increasing horizons and aggregate budgets. Compare scheduler effects separately from GCTS effects.'};
 writeFileSync(`${directory}/manifest.json`,JSON.stringify(manifest));
 for(const lane of lanes){
  const child=spawnSync(process.execPath,[fileURLToPath(import.meta.url),`--directory=${directory}`,`--worker=${lane.id}`],{stdio:'inherit'});if(child.status!==0)throw Error(`Worker failed ${lane.id}`);
  lane.runs=readFileSync(`${directory}/${lane.id}.jsonl`,'utf8').trim().split('\n').map(JSON.parse);
 }
 manifest.incomplete=false;
 manifest.summary=lanes.map(l=>({lane:l.id,identified:l.runs.filter(r=>r.certificate).length,unknown:l.runs.filter(r=>!r.certificate).length,totalMs:l.runs.reduce((n,r)=>n+r.totalMs,0),nodes:l.runs.reduce((n,r)=>n+r.stats.nodes,0),branches:l.runs.reduce((n,r)=>n+r.stats.branches,0),maxRSSKiB:Math.max(...l.runs.map(r=>r.maxRSSKiB))}));
 writeFileSync(get('output','research/knot-classifier/lattice-path-schedules-benchmark.json'),JSON.stringify(manifest)+'\n');console.log(JSON.stringify({summary:manifest.summary}));
}
