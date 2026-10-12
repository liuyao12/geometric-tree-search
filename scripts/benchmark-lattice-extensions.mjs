import {readFileSync,writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {scrambleLattice} from '../research/knot-classifier/lattice-scramble.mjs';
import {solveLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
const args=process.argv.slice(2),get=(k,d)=>args.find(a=>a.startsWith(`--${k}=`))?.slice(k.length+3)??d;
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url)));
const ids=get('knots','3_1,4_1,5_1').split(','),steps=Number(get('steps',3)),maxDepth=Number(get('depth',steps*2));
const worker=get('lane',null);
if(worker){
 const model=worker==='extension-transfer'?new LocalPointMarkings():null,extensionModel=worker==='extension-transfer'?new LocalExtensionMarkings():null,runs=[];
 for(let i=0;i<ids.length;i++){
  const record=corpus.records.find(r=>r.id===ids[i]);if(!record)throw Error('Unknown evaluator reference.');
  const source=scrambleLattice(record.vertices,{steps,seed:43+i*101,maxEdges:220}),target=scrambleLattice(record.vertices,{steps,seed:901+i*103,maxEdges:220});
  const result=solveLatticeLazy(source.vertices,target.vertices,{maxDepth,maxEdges:220,learn:worker!=='unmarked',model,extensionLearn:worker.startsWith('extension-'),extensionModel,seed:31,nodeCap:Number(get('node-cap',5000)),stateCap:200000,region:null});
  runs.push({evaluatorKnot:record.id,sourceSeed:source.seed,targetSeed:target.seed,source:source.vertices,target:target.vertices,sourceDiagram:source.finalDiagram,targetDiagram:target.finalDiagram,provenance:[source.provenance,target.provenance],...result});
 }
 console.log(JSON.stringify({lane:worker,runs,runtime:{node:process.version,maxRSSKiB:process.resourceUsage().maxRSS,memoryAtEndBytes:process.memoryUsage()}}));
}else{
 const lanes=[];
 for(const lane of get('lanes','unmarked,extension-cold,extension-transfer').split(',')){
  const child=spawnSync(process.execPath,[fileURLToPath(import.meta.url),`--lane=${lane}`,`--knots=${ids.join(',')}`,`--steps=${steps}`,`--depth=${maxDepth}`,`--node-cap=${get('node-cap',5000)}`],{encoding:'utf8',maxBuffer:32*1024*1024});
  if(child.status!==0)throw Error(child.stderr||'Benchmark worker failed');
  const result=JSON.parse(child.stdout);lanes.push(result);
  const checkpoint=get('output',null);if(checkpoint)writeFileSync(checkpoint,JSON.stringify({incomplete:true,version:'lattice-local-extension-benchmark-v1',stepsPerIndependentScramble:steps,maxDepth,region:null,lanes})+'\n');
  for(const run of result.runs)console.log(JSON.stringify({lane,knot:run.evaluatorKnot,status:run.status,moves:run.certificate?.steps.map(s=>s.kind),nodes:run.stats?.nodes,branches:run.stats?.branches,extensionEliminations:run.stats?.extensionEliminations,extensionPrototypes:run.extensions?.prototypes,extensionProbeNodes:run.extensions?.probeNodesThisRun,extensionProbeMs:run.extensions?.probeMsThisRun,raw:run.stats?.rawCandidates,states:run.stats?.generatedStates,markingEliminations:run.stats?.markingEliminations,initialVersion:run.learning?.initialVersion,localSamples:run.learning?.eventsThisRun.reduce((n,e)=>n+e.samples.length,0),totalMs:run.totalMs}));
 }
 const report={incomplete:false,nodeCap:Number(get('node-cap',5000)),stateCap:200000,maxEdges:220,version:'lattice-local-extension-benchmark-v1',stepsPerIndependentScramble:steps,maxDepth,region:null,lanes,scope:'All lattice face placements throughout both knots. Provenance not passed to search. Separate fresh Node worker per lane. Transfer lane shares only its in-memory local marking model across different knot tests. No bundled marking import.'};
 const output=get('output',null);if(output)writeFileSync(output,JSON.stringify(report)+'\n');
 if(lanes.some(l=>l.runs.some(r=>r.status!=='equivalent')))process.exitCode=1;
}
