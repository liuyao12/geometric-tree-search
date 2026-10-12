// Reproducible evaluation harness. Knot labels and scramble histories stay here.
import {readFileSync,writeFileSync,appendFileSync,mkdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {scrambleLattice} from '../research/knot-classifier/lattice-scramble.mjs';
import {solveLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
const args=process.argv.slice(2),get=(k,d)=>args.find(a=>a.startsWith(`--${k}=`))?.slice(k.length+3)??d;
const directory=get('directory','/private/tmp/knot-through8'),worker=get('lane',null);
mkdirSync(directory,{recursive:true});
const manifestPath=`${directory}/manifest.json`;
if(worker){
 const manifest=JSON.parse(readFileSync(manifestPath)),marked=worker==='extension-transfer';
 if(!marked&&worker!=='unmarked')throw Error('Unknown lane');
 const model=marked?new LocalPointMarkings():null,extensionModel=marked?new LocalExtensionMarkings({probeNodeCap:manifest.bounds.extensionProbeNodeCap}):null;
 const destination=`${directory}/${worker}.jsonl`;writeFileSync(destination,'');
 for(const [caseIndex,c]of manifest.cases.entries()){
  const result=solveLatticeLazy(c.source,c.target,{...manifest.bounds,learn:marked,model,extensionModel});
  // Preserve each new proof once; cumulative catalogs are not repeated per case.
  if(result.extensions)delete result.extensions.events;
  if(result.learning)delete result.learning.events;
  const run={caseIndex,...result,maxRSSKiB:process.resourceUsage().maxRSS};
  appendFileSync(destination,JSON.stringify(run)+'\n');
  console.log(JSON.stringify({lane:worker,caseIndex,knot:c.evaluatorKnot,seedPair:c.seedPair,status:run.knotEquivalence,reason:run.reason,moves:run.certificate?.steps.length,nodes:run.stats?.nodes,branches:run.stats?.branches,options:run.stats?.availableCandidates,eliminations:run.stats?.extensionEliminations,initialVersion:run.extensions?.initialVersion,prototypes:run.extensions?.prototypes,totalMs:run.totalMs,validationMs:run.extensions?.transferValidationMsThisRun}));
 }
 writeFileSync(`${directory}/${worker}-runtime.json`,JSON.stringify({node:process.version,maxRSSKiB:process.resourceUsage().maxRSS,memoryAtEndBytes:process.memoryUsage()}));
}else{
 const started=performance.now(),corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url)));
 const selected=get('knots',null),records=selected?selected.split(',').map(id=>corpus.records.find(r=>r.id===id)):corpus.records.filter(r=>r.crossings>=3&&r.crossings<=8);
 const steps=Number(get('steps',5)),seeds=Number(get('seeds',3));
 const bounds={maxDepth:2*steps,maxEdges:240,region:null,seed:31,nodeCap:Number(get('node-cap',200)),stateCap:30000,maxMs:Number(get('max-ms',6000)),extensionProbeNodeCap:512};
 const cases=[];
 for(const [i,record]of records.entries())for(let j=0;j<seeds;j++){
  if(!record)throw Error('Missing evaluator knot');
  const sourceSeed=43+i*101+j*10007,targetSeed=901+i*103+j*20011;
  const source=scrambleLattice(record.vertices,{steps,seed:sourceSeed,maxEdges:bounds.maxEdges}),target=scrambleLattice(record.vertices,{steps,seed:targetSeed,maxEdges:bounds.maxEdges});
  cases.push({evaluatorKnot:record.id,crossings:record.crossings,seedPair:j,sourceSeed,targetSeed,source:source.vertices,target:target.vertices,sourceDiagram:source.finalDiagram,targetDiagram:target.finalDiagram,provenance:[source.provenance,target.provenance]});
  console.log(JSON.stringify({prepared:cases.length,knot:record.id,seedPair:j}));
 }
 const manifest={version:'lattice-through8-multiseed-v1',stepsPerIndependentScramble:steps,region:null,bounds,cases,preparationMs:performance.now()-started,scope:'All incident lattice faces, no patch region. Same fixed projection and single-move grammar in both lanes. Exact coordinates; no alignment quotient. Five-move self-avoiding walks need not have minimum distance five. Labels and histories are evaluation-only. Sequential fresh worker per lane, with a cold model at the start of the transfer lane and in-memory reuse across all subsequent knot types and seeds. Budgets include learning and transfer verification. Partial enumeration and interrupted probes are unknown. No invariant, reference label, prelearned model, or construction path enters search.'};
 writeFileSync(manifestPath,JSON.stringify(manifest));
 const lanes=[];
 for(const lane of ['unmarked','extension-transfer']){
  const child=spawnSync(process.execPath,[fileURLToPath(import.meta.url),`--lane=${lane}`,`--directory=${directory}`],{stdio:'inherit'});
  if(child.status!==0)throw Error(`Worker failed: ${lane}; completed cases remain in ${directory}`);
  lanes.push({lane,runs:readFileSync(`${directory}/${lane}.jsonl`,'utf8').trim().split('\n').map(JSON.parse),runtime:JSON.parse(readFileSync(`${directory}/${lane}-runtime.json`))});
 }
 const report={...manifest,incomplete:false,lanes,experimentMs:performance.now()-started};
 const sum=(runs,key)=>runs.reduce((n,r)=>n+(r[key]||0),0);
 report.summary=lanes.map(l=>({lane:l.lane,cases:l.runs.length,success:l.runs.filter(r=>r.certificate).length,unknown:l.runs.filter(r=>!r.certificate).length,totalMs:sum(l.runs,'totalMs'),verificationMs:sum(l.runs,'verificationMs'),nodes:l.runs.reduce((n,r)=>n+(r.stats?.nodes||0),0),branches:l.runs.reduce((n,r)=>n+(r.stats?.branches||0),0),availableCandidates:l.runs.reduce((n,r)=>n+(r.stats?.availableCandidates||0),0),extensionEliminations:l.runs.reduce((n,r)=>n+(r.stats?.extensionEliminations||0),0),probeMs:l.runs.reduce((n,r)=>n+(r.extensions?.probeMsThisRun||0)+(r.learning?.probeMsThisRun||0),0),transferValidationMs:l.runs.reduce((n,r)=>n+(r.extensions?.transferValidationMsThisRun||0)+(r.learning?.transferValidationMsThisRun||0),0),maxRSSKiB:l.runtime.maxRSSKiB}));
 writeFileSync(get('output','research/knot-classifier/lattice-through8-benchmark.json'),JSON.stringify(report)+'\n');
 console.log(JSON.stringify({summary:report.summary,experimentMs:report.experimentMs}));
}
