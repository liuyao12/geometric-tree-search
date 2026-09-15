// Register intrinsic cloud-marked motifs into the existing finite observed pool.
// Target-state tables propose poses only; no state labels enter marking values.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {portableWitnessCheck} from './portable-cloud-filter.mjs';
const [compiledPath,junctionPath,joinedPath,portablePath,alternativePath,out]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const compiled=JSON.parse(readFileSync(compiledPath)),junctions=JSON.parse(readFileSync(junctionPath)),joined=JSON.parse(readFileSync(joinedPath)),portable=JSON.parse(readFileSync(portablePath)),alternatives=JSON.parse(readFileSync(alternativePath));
assert.equal(portable.jointGeometryHash,hash(joinedPath));assert.equal(joined.junctionHash,hash(junctionPath));assert.equal(portable.inputHash,compiled.inputHash);assert.equal(portable.learningHash,compiled.learningHash);assert.equal(joined.alternativeHash,hash(alternativePath));
const clouds=[],cloudIndex=new Map(),models=[],checks=[];
const rotate=(v,r)=>[0,1,2].map(j=>v.reduce((sum,x,i)=>sum+x*r[i][j],0));
function intern(cloud){const key=JSON.stringify(cloud);if(!cloudIndex.has(key)){cloudIndex.set(key,clouds.length);clouds.push(cloud);}return cloudIndex.get(key);}
for(const input of compiled.models){
 const edges=new Map(joined.folds[input.fold].edges.map(e=>[e.candidate,e])),nodes=new Map(junctions.folds[input.fold].nodes.map(n=>[n.point,n]));
 const candidates=[],lookup=new Map(),byBase=new Map();
 for(const base of input.candidates){
  const cid=Number(base.id),edge=edges.get(cid),variants=edge?edge.geometricWitnesses.map((w,i)=>({w,states:edge.allowedPresentStates[i]})):[{w:null,states:[]}];
  const dedup=new Map();
  for(const {w,states} of variants){
   const cloudM=w?edge.points.map((point,side)=>{
    const value=portable.motifs[w.template].cloudM[side];return {point:String(point),cloud:intern({vectors:value.vectors.map(v=>rotate(v,w.rotationRow)),colors:value.colors})};
   }):[];
   const key=JSON.stringify(cloudM);let id=dedup.get(key);
   if(id===undefined){id=String(candidates.length).padStart(8,'0');dedup.set(key,id);candidates.push({id,base:base.id,t:base.t,m:base.m.filter(m=>m.channel==='0'),cloudM,registration:w?{template:w.template,rotationRow:w.rotationRow}:null});if(!byBase.has(base.id))byBase.set(base.id,id);}
   lookup.set(JSON.stringify([base.id,states]),id);
  }
 }
 const model={capacity:input.capacity,cloudRadius:portable.markingRadiusAngstrom,required:input.required,candidates};
 const live={...model,candidates:candidates.map(c=>({...c,cloudM:c.cloudM.map(m=>({...m,cloud:clouds[m.cloud]}))}))};
 const records=[{name:'original',selected:input.trainingSelected.map(Number)},...alternatives.runs.filter(r=>r.fold===input.fold).map(r=>({name:`alternative-${r.seed}`,selected:r.selected}))];
 const lifts=[];
 for(const record of records){
  const chosen=new Set(record.selected),labels=new Map([...nodes].map(([p,n])=>[p,n.states.findIndex(s=>s.candidates.length===n.incident.filter(e=>chosen.has(e.candidate)).length&&s.candidates.every(i=>chosen.has(i)))]));
  const selected=record.selected.map(cid=>{const base=String(cid).padStart(6,'0'),edge=edges.get(cid),states=edge?edge.points.map(p=>labels.get(p)):[];const id=lookup.get(JSON.stringify([base,states]));assert(id!==undefined);return id;});
  const check=portableWitnessCheck(live,new Set(selected));assert(check.valid);lifts.push({name:record.name,selected,verifiedCommonValues:check.witnesses.length});
 }
 models.push({fold:input.fold,file:input.file,model,trainingLifts:lifts});
 checks.push({file:input.file,baseCandidates:input.candidates.length,registeredVariants:candidates.length,representedBasePlacements:byBase.size,trainingRecords:lifts.length,verifiedCommonValues:lifts.reduce((n,l)=>n+l.verifiedCommonValues,0)});
 console.log(JSON.stringify(checks.at(-1)));
}
writeFileSync(out,JSON.stringify({scope:'Finite registered portable-cloud model; old state tables propose registrations only. No target-state m labels. Uncoupled edges have no cloud decoration. Not a complete continuous-pose pool.',compiledHash:hash(compiledPath),junctionHash:hash(junctionPath),joinedHash:hash(joinedPath),portableHash:hash(portablePath),alternativeHash:hash(alternativePath),sourceHash:hash(new URL(import.meta.url)),clouds,models,checks}),{flag:'wx'});
