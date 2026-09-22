#!/usr/bin/env node
import fs from 'node:fs';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {a2Transform,SparseA2Marking,NoA2Marking,solveA2Tiling,makeHexBoundary} from '../assets/a2-tiling-engine.js';
import {parity,compact} from '../assets/tile-connection-learning.js';

globalThis.requestAnimationFrame??=cb=>setImmediate(cb);
export class SatWorker{
 constructor(){this.process=spawn(process.env.PYTHON??'python3',[fileURLToPath(new URL('./a2_online_marking_sat.py',import.meta.url))],{stdio:['pipe','pipe','inherit']});this.pending=[];createInterface({input:this.process.stdout}).on('line',line=>{const p=this.pending.shift();if(p){const r=JSON.parse(line);r.status==='error'?p.reject(Error(r.message)):p.resolve(r);}});this.process.on('exit',code=>{for(const p of this.pending.splice(0))p.reject(Error(`SAT worker exited ${code}`));});}
 call(request){return new Promise((resolve,reject)=>{this.pending.push({resolve,reject});this.process.stdin.write(JSON.stringify(request)+'\n');});}
 close(){this.process.stdin.end();}
}
export function supportDomain(learner,halo){return learner.config.tiles.flatMap(tile=>learner.pointDomain(tile,halo).flatMap(point=>[0,1,2].map(component=>({tile,point,component}))));}
export function overlapContacts(learner,domain,patch){
 const sections=new Map(),pairs=new Map();for(const spec of patch){const p=learner.materialize(spec),sym=p.orientation.symmetry,sign=parity(sym.permutation);domain.forEach((e,i)=>{if(e.tile!==p.tile)return;const key=`${a2Transform(e.point,sym).map((v,j)=>v+p.translation[j])}|${sym.permutation.indexOf(e.component)}`;if(!sections.has(key))sections.set(key,[]);for(const old of sections.get(key)){const a=Math.min(i,old.i),b=Math.max(i,old.i),s=sign*old.sign;pairs.set(`${a}:${b}:${s}`,[a,b,s]);}sections.get(key).push({i,sign});});}return [...pairs.values()];
}
export class NeutralMarking extends SparseA2Marking{score(){return 0;}}
export async function probePair(learner,pair,{support=[],seed=1,nodes=5000,ms=1500}={}){
 const started=performance.now();if(!learner.verifyPatch([pair.root,pair.attachment],support).compatible)return {status:'restricted',result:'no',reason:'marking rejects fixed pair',nodes:0,backtracks:0,elapsedMs:performance.now()-started,verificationMs:0,placements:[]};
 const stopToken={stop:false},timer=setTimeout(()=>{stopToken.stop=true;},ms);let result;
 try{result=await solveA2Tiling({boundary:makeHexBoundary(10),tiles:learner.config.tiles,allowReflections:learner.config.allowReflections,latticePointFilter:learner.pointFilter,initialPlacements:[pair.root,pair.attachment].map(learner.materialize),fixedInitialPlacements:true,completePointGrowth:true,requiredPoints:learner.corePoints([pair.root,pair.attachment]),requireViableFrontier:true,maximize:true,targetPlacements:Infinity,nodeLimit:nodes,randomSeed:seed,marking:support.length?new NeutralMarking(support):new NoA2Marking(),stopToken});}finally{clearTimeout(timer);}
 const elapsedMs=performance.now()-started,placements=compact(result.placements),verifyStart=performance.now();
 if(result.result==='yes'&&(!learner.verifyCorona([pair.root,pair.attachment],placements).complete||!learner.verifyPatch(placements,support).compatible))throw Error('Positive witness failed independent replay');
 return {status:result.result==='yes'?'valid':result.result==='no'?'invalid':'unresolved',result:result.result,nodes:result.stats.nodes,backtracks:result.stats.backtracks,elapsedMs,verificationMs:performance.now()-verifyStart,placements};
}
export function shuffle(items,seed){let state=seed>>>0;const out=[...items];for(let i=out.length-1;i>0;i--){state=(Math.imul(1664525,state)+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[out[i],out[j]]=[out[j],out[i]];}return out;}
export async function runOnline({tile='hat',mode='online',orderSeed=1,positiveMode='pair',limit=Infinity,pairMs=1500,probeMs=150,probeNodes=128,timeoutMs=500,onRow=()=>{}}={}){
 const started=performance.now(),learner=createCoronaLearner(tile,{lattice:'turtle-sublattice'}),pairs=shuffle(learner.connections(),orderSeed).slice(0,limit),worker=mode==='online'?new SatWorker():null;
 let domain=supportDomain(learner,1),halo=1,support=[],modelStatus='empty',solverVersion=null,trainingMs=0,replayMs=0,fallbacks=0,rescuedPositives=0,falseNegativeIfTrusted=0,markedWitnesses=0;
 const rows=[],snapshots=[],observations=[];
 const encode=row=>({positive:row.status==='valid',contacts:overlapContacts(learner,domain,row.status==='valid'&&positiveMode==='witness'?row.placements:[row.root,row.attachment])});
 const reset=async()=>{domain=supportDomain(learner,halo);const ready=await worker.call({op:'init',n:domain.length,timeoutMs});solverVersion=ready.z3;return worker.call({op:'solve',constraints:observations.map(encode)});};
 try{
  if(worker){const t=performance.now();await reset();trainingMs+=performance.now()-t;}
  for(const [index,pair]of pairs.entries()){
   const seed=(Math.imul(index+1,1987)^orderSeed)>>>0,previousSupport=support,priorStatus=modelStatus;let guided=null,oracle=null;
   if(mode==='online'&&support.length){guided=await probePair(learner,pair,{support,seed,nodes:probeNodes,ms:probeMs});if(guided.status==='valid')markedWitnesses++;}
   if(!guided||guided.status!=='valid'){if(guided)fallbacks++;oracle=await probePair(learner,pair,{seed,nodes:5000,ms:pairMs});if(guided&&oracle.status==='valid'){rescuedPositives++;if(['restricted','invalid'].includes(guided.status))falseNegativeIfTrusted++;}}
   // Only an unmarked exhausted search establishes a negative. A marking
   // rejection / marked exhaustion / timeout supplies no negative label.
   const outcome=guided?.status==='valid'?guided:oracle,row={index,root:pair.root,attachment:pair.attachment,status:outcome.status,placements:outcome.placements,guided,oracle,priorStatus,priorValues:previousSupport.length};
   let update=null;
   if(worker&&row.status!=='unresolved'){
    observations.push(row);const t=performance.now();update=await worker.call({op:'solve',constraints:[encode(row)]});
    if(update.status==='unsat'&&halo<3){halo++;update=await reset();}
    trainingMs+=performance.now()-t;modelStatus=update.status;
    support=update.status==='sat'?domain.flatMap((e,i)=>update.values[i]===null?[]:[{...e,value:update.values[i]}]):[];
    const replayStart=performance.now();for(const old of observations){const patch=old.status==='valid'&&positiveMode==='witness'?old.placements:[old.root,old.attachment],compatible=learner.verifyPatch(patch,support).compatible;if(update.status==='sat'&&compatible!==(old.status==='valid'))throw Error('Synthesized marking misclassifies an observed constraint');}replayMs+=performance.now()-replayStart;
   }
   row.update=update?{status:update.status,solveMs:update.solveMs,halo,values:support.length}:null;rows.push(row);
   // Each saved revision includes the exact evidence prefix; no future labels.
   if([8,16,32,64,128,256].includes(index+1)||index===pairs.length-1)snapshots.push({after:index+1,support,halo,status:modelStatus,observedPositive:observations.filter(r=>r.status==='valid').length,observedNegative:observations.filter(r=>r.status==='invalid').length});
   onRow({index:index+1,total:pairs.length,status:row.status,guided:guided?.status??null,oracle:oracle?.status??null,values:support.length,halo,update:row.update?.status??null});
  }
 }finally{worker?.close();}
 return {tile,mode,positiveMode,orderSeed,protocol:{lattice:'index3',reflections:true,rank:3,pairMs,pairNodes:5000,probeMs,probeNodes,solverTimeoutMs:timeoutMs,solverVersion,score:'zero',knownMarking:false,negativeAuthority:'exhausted unmarked pair-corona search only'},counts:{total:rows.length,valid:rows.filter(r=>r.status==='valid').length,invalid:rows.filter(r=>r.status==='invalid').length,unresolved:rows.filter(r=>r.status==='unresolved').length,markedWitnesses,fallbacks,rescuedPositives,falseNegativeIfTrusted},timing:{elapsedMs:performance.now()-started,trainingMs,replayMs,searchMs:rows.reduce((s,r)=>s+(r.guided?.elapsedMs??0)+(r.oracle?.elapsedMs??0),0),witnessReplayMs:rows.reduce((s,r)=>s+(r.guided?.verificationMs??0)+(r.oracle?.verificationMs??0),0)},nodes:rows.reduce((s,r)=>s+(r.guided?.nodes??0)+(r.oracle?.nodes??0),0),rows,snapshots};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const a=Object.fromEntries(process.argv.slice(2).map(s=>s.replace(/^--/,'').split('='))),out=a.out??'/tmp/a2-online-pairs';fs.mkdirSync(out,{recursive:true});
 const options={tile:a.tile??'hat',mode:a.mode??'online',orderSeed:+(a.seed??1),positiveMode:a.positive??'pair',limit:+(a.limit??Infinity),pairMs:+(a.ms??1500),probeMs:+(a['probe-ms']??150),probeNodes:+(a['probe-nodes']??128),timeoutMs:+(a['sat-ms']??500),onRow:r=>{if(r.index%16===0||r.index===r.total)console.log(JSON.stringify(r));}};
 const result=await runOnline(options),file=`${out}/${result.tile}-${result.mode}-${result.positiveMode}-s${result.orderSeed}.json`;fs.writeFileSync(file,JSON.stringify(result));console.log(JSON.stringify({file,counts:result.counts,timing:result.timing,nodes:result.nodes}));
}
