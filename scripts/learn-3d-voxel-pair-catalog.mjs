// Complete-catalogue research with exact pair symmetry and explicit checkpoints.
// Learned assignments and full witnesses stay in the selected output directory.
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {readFile,writeFile,mkdir,rename} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {verifyCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {OnlineMarking,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
import {pairOrbits,transportPatch} from './lib/3d-pair-orbits.mjs';
import {verifyPointObstruction} from './lib/verify-point-obstruction.mjs';
const execute=promisify(execFile),args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('='))),tile=args.tile??'p9-48258';
const record=tile==='cube'?{voxels:[[0,0,0]]}:POLYCUBE_GCTS_CANDIDATES.find(t=>t.id===tile);if(!record)throw Error('Unknown catalogue tile');
const frontierBatch=Number(args['frontier-batch']??1),oracle=args.oracle??'z3';
if(!['z3','glucose'].includes(oracle))throw Error('Unknown oracle');
const timeMs=Number(args['pair-ms']??5000),frontier=args.frontier??'nogood',maxGroups=Number(args['max-groups']??100000),output=args.output??`/tmp/gcts-orbits-${tile}`;
if(!Number.isSafeInteger(frontierBatch)||frontierBatch<1||!Number.isSafeInteger(timeMs)||timeMs<1||!Number.isSafeInteger(maxGroups)||maxGroups<1||!['nogood','occupancy'].includes(frontier))throw Error('Invalid oracle options');
await mkdir(output,{recursive:true});
if(oracle==='glucose'&&frontier!=='occupancy')throw Error('Glucose oracle requires occupancy frontier');
const started=performance.now(),model=prepareVoxelPointModel(record.voxels,{name:tile,radius:1}),orbits=pairOrbits(model),sha=x=>createHash('sha256').update(x).digest('hex');
const modelSha=sha(JSON.stringify(model)),orbitSha=sha(JSON.stringify(orbits.groups)),sources={};
for(const p of ['scripts/learn-3d-voxel-pair-catalog.mjs','scripts/solve_point_pair_corona.py','scripts/solve_voxel_pair_corona.py','scripts/certify_voxel_obstruction.py','scripts/lib/3d-pair-orbits.mjs','scripts/lib/verify-point-obstruction.mjs','apps/3d-lattice-tiler/voxel-point-model.js','apps/3d-lattice-tiler/corona-graph.js','apps/3d-lattice-tiler/marking-learning.js','apps/3d-lattice-tiler/v2/search.js'])sources[p]=sha(await readFile(new URL('../'+p,import.meta.url)));
let checkpoint;try{checkpoint=JSON.parse(await readFile(`${output}/checkpoint.json`));}catch(e){if(e.code!=='ENOENT')throw e;}
if(checkpoint){
 if(args.parent||args.resolved)throw Error('Parent/import evidence requires a fresh output directory');
 if(args.resume!=='true')throw Error('Output already contains a checkpoint; use --resume=true explicitly');
 if(checkpoint.modelSha!==modelSha||checkpoint.orbitSha!==orbitSha||JSON.stringify(checkpoint.sources)!==JSON.stringify(sources))throw Error('Checkpoint model, orbits or source version changed');
}else checkpoint={tile,modelSha,orbitSha,sources,runs:[],groups:{}};
// Explicitly fork a historical receipt when the oracle source changes. Retain
// its source hashes and run costs; verify every inherited artifact before use.
if(args.parent){
 const parentRaw=await readFile(`${args.parent}/checkpoint.json`),parent=JSON.parse(parentRaw);
 if(parent.modelSha!==modelSha||parent.orbitSha!==orbitSha)throw Error('Parent geometry or pair catalogue changed');
 checkpoint.parents=[...(parent.parents??[]),{checkpointSha256:sha(parentRaw),sources:parent.sources,runs:parent.runs}];
 for(const [gi,entry] of Object.entries(parent.groups)){
  const raw=await readFile(`${args.parent}/${entry.file}`);if(sha(raw)!==entry.sha256||JSON.parse(raw).status!==entry.status)throw Error('Parent artifact changed');
  const file=`inherited-${gi}.json`;await writeFile(`${output}/${file}`,raw);checkpoint.groups[gi]={...entry,file};
 }
}
if(args.resolved){
 if(!args.parent)throw Error('Imported refinements require an explicit parent checkpoint');
 const manifestRaw=await readFile(args.resolved),manifest=JSON.parse(manifestRaw);checkpoint.importedEvidence={manifestSha256:sha(manifestRaw),sources:manifest.sources,rows:[]};
 for(const entry of manifest.rows){
  const gi=entry.orbit,prior=checkpoint.groups[gi];if(!Number.isInteger(gi)||!prior)throw Error('Imported orbit is not in parent');
  const before=JSON.parse(await readFile(`${output}/${prior.file}`)),raw=await readFile(entry.file),result=JSON.parse(raw);
  if(sha(raw)!==entry.sha256||!before.problemSha256||result.problemSha256!==before.problemSha256)throw Error('Imported result belongs to another problem');
  if(!['valid','invalid','unresolved'].includes(result.status)||before.status!=='unresolved'&&result.status!==before.status)throw Error('Imported evidence conflicts with a resolved label');
  const file=`imported-${gi}.json`;await writeFile(`${output}/${file}`,raw);checkpoint.groups[gi]={file,sha256:sha(raw),status:result.status};checkpoint.importedEvidence.rows.push({orbit:gi,sha256:sha(raw),status:result.status});
 }
}

const run={timeMs,frontier,frontierBatch,oracle,startedAt:new Date().toISOString(),attempted:0};checkpoint.runs.push(run);
async function save(){await writeFile(`${output}/checkpoint-next.json`,JSON.stringify(checkpoint));await rename(`${output}/checkpoint-next.json`,`${output}/checkpoint.json`);}
const labels=Array(orbits.pairs.length),groupReport=[];
for(let gi=0;gi<orbits.groups.length;gi++){
 const group=orbits.groups[gi],prior=checkpoint.groups[gi];let result;
 if(prior){const raw=await readFile(`${output}/${prior.file}`);if(sha(raw)!==prior.sha256)throw Error('Checkpoint artifact changed');result=JSON.parse(raw);}
 if((!result||result.status==='unresolved')&&run.attempted<maxGroups){
  const inputFile=`${output}/pair-${gi}.json`,resultFile=`${output}/result-${gi}-run-${checkpoint.runs.length}.json`;
  await writeFile(inputFile,JSON.stringify({model,pair:group.pair}));
  const command=[fileURLToPath(new URL(oracle==='glucose'?'./solve_voxel_pair_corona.py':'./solve_point_pair_corona.py',import.meta.url)),`--input=${inputFile}`,`--output=${resultFile}`,`--time-ms=${timeMs}`,`--frontier-batch=${frontierBatch}`];
  if(oracle==='z3')command.push('--encoding=voxel-cover',`--frontier=${frontier}`);
  // Only a terminal unresolved occupancy run can supply saved necessary point
  // constraints; the Python oracle rebuilds them and checks the problem hash.
  if(prior&&result.stats?.frontier==='occupancy'&&frontier==='occupancy')command.push(`--resume=${output}/${prior.file}`);
  try{
   await execute(args.python??'python3',command,{timeout:timeMs+15000,maxBuffer:1048576});
   result=JSON.parse(await readFile(resultFile));
  }catch(e){result={status:'unresolved',reason:e.killed?'process time limit':e.message,placements:group.pair,stats:{},nogoods:[]};await writeFile(resultFile,JSON.stringify(result));}
  const raw=await readFile(resultFile);checkpoint.groups[gi]={file:resultFile.slice(output.length+1),sha256:sha(raw),status:result.status};run.attempted++;await save();
 }
 result??={status:'unresolved',reason:'catalogue pass limit',stats:{},nogoods:[]};
 for(const n of result.nogoods??[])verifyPointObstruction(model,n);
 for(const member of group.members){
  if(result.status==='valid'){
   const placements=transportPatch(result.placements,member,orbits.transforms);
   if(!verifyCorona(model,member.pair,placements).complete||!verifyVoxelPatch(model,placements,{requireTarget:false}).ok)throw Error('Transported positive failed independent replay');
  }
  labels[member.index]={pair:member.pair,status:result.status,orbit:gi};
 }
 const row={orbit:gi,pair:group.pair,members:group.members.length,status:result.status,reason:result.reason,stats:result.stats};groupReport.push(row);
 console.log(JSON.stringify({tile,...row}));
}
const trainer=new OnlineMarking(model,orbits.transforms);let marking;
for(const row of labels)marking=trainer.add(row);
marking=trainer.snapshot({maxEvaluations:2048});
let positivePassed=0,negativeBlocked=0;
for(const row of labels){const compatible=pairCompatible(marking.fields,row.pair);if(row.status==='valid'&&compatible)positivePassed++;if(row.status==='invalid'&&!compatible)negativeBlocked++;}
if(positivePassed!==marking.counts.valid||positivePassed!==marking.positivePassed||negativeBlocked!==marking.negativeBlocked)throw Error('Independent marking classification failed');
marking.complete=!marking.counts.unresolved;
marking.accepted=marking.complete&&marking.counts.valid>0&&(marking.counts.invalid===0||negativeBlocked*2>marking.counts.invalid);
let growth=null;
if(marking.accepted){
 const marked={...model,orientations:model.orientations.map((o,i)=>({...o,marks:marking.fields[i]}))};
 for await(const e of search(marked,{mode:'gcts',learnedRestriction:true,timeMs:20000,nodes:10000,seed:1}))growth=e;
 if(growth.result==='finite_exact'&&(!verify(marked,growth.placements).ok||!verifyVoxelPatch(model,growth.placements).ok))throw Error('Marked growth replay failed');
}
run.elapsedMs=performance.now()-started;await save();
await writeFile(`${output}/learning.json.gz`,gzipSync(JSON.stringify({model,labels,marking,growth})));
const summary={protocol:{tile,modelSha,orbitSha,sources,runs:checkpoint.runs,parents:checkpoint.parents??[],importedEvidence:checkpoint.importedEvidence??null,oracle:`Validated binary-cover ${oracle==='glucose'?'incremental Glucose':'Z3 PB/SAT'} control with viable frontier; exact proper-rotation and seed-exchange orbits`,scope:'Local pair labels and a learned restriction. Neither infinite construction nor aperiodicity proof.'},pairs:labels.length,orbits:orbits.groups.length,groups:groupReport,learning:{complete:marking.complete,accepted:marking.accepted,counts:marking.counts,positivePassed,negativeBlocked,points:marking.points,values:marking.values},growth:growth?{result:growth.result,verification:growth.verification,stats:growth.stats}:null};
await writeFile(`${output}/summary.json`,JSON.stringify(summary,null,2)+'\n');console.log(JSON.stringify({...summary.learning,pairs:labels.length,orbits:orbits.groups.length,growth:summary.growth?.result??null}));
