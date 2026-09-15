// Geometry-only registrations determine candidates. Known selections are used
// only AFTER the pool is fixed, to check that the training fillings still lift.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {portableWitnessCheck} from './portable-cloud-filter.mjs';
const [compiledPath,portablePath,registrationPath,alternativePath,out]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const compiled=JSON.parse(readFileSync(compiledPath)),portable=JSON.parse(readFileSync(portablePath)),geometry=JSON.parse(readFileSync(registrationPath)),alternatives=JSON.parse(readFileSync(alternativePath));
assert.equal(geometry.portableHash,hash(portablePath));assert.equal(geometry.inputHash,compiled.inputHash);assert.equal(alternatives.learningHash,portable.learningHash);
const clouds=[],interned=new Map(),models=[],checks=[];
const rotate=(v,r)=>[0,1,2].map(j=>v.reduce((s,x,i)=>s+x*r[i][j],0));
function intern(value){const key=JSON.stringify(value);if(!interned.has(key)){interned.set(key,clouds.length);clouds.push(value);}return interned.get(key);}
for(const input of compiled.models){
 const edges=new Map(geometry.folds[input.fold].edges.map(e=>[e.candidate,e])),candidates=[],liftLookup=new Map();
 for(const base of input.candidates){
  const cid=Number(base.id),edge=edges.get(cid),dedup=new Map();
  for(const registration of edge?edge.registrations:[null]){
   const cloudM=registration?edge.points.map((point,side)=>{const c=portable.motifs[registration.template].cloudM[side];return {point:String(point),cloud:intern({vectors:c.vectors.map(v=>rotate(v,registration.rotationRow)),colors:c.colors})};}):[];
   const key=JSON.stringify(cloudM);let id=dedup.get(key);
   if(id===undefined){id=String(candidates.length).padStart(8,'0');dedup.set(key,id);candidates.push({id,base:base.id,t:base.t,m:base.m.filter(m=>m.channel==='0'),cloudM,registration:registration?{template:registration.template,rotationRow:registration.rotationRow}:null});}
   if(!liftLookup.has(cid))liftLookup.set(cid,[]);liftLookup.get(cid).push({id,arms:registration?.selectedArms??[]});
  }
 }
 const model={capacity:input.capacity,required:input.required,cloudRadius:portable.markingRadiusAngstrom,candidates};
 // Training validation does not add, remove or reorder any candidate.
 const live={...model,candidates:candidates.map(c=>({...c,cloudM:c.cloudM.map(m=>({...m,cloud:clouds[m.cloud]}))}))};
 const records=[{name:'original',selected:input.trainingSelected.map(Number)},...alternatives.runs.filter(r=>r.fold===input.fold).map(r=>({name:`alternative-${r.seed}`,selected:r.selected}))];
 const trainingLifts=records.map(record=>{
  const chosen=new Set(record.selected),selected=record.selected.map(cid=>{const row=liftLookup.get(cid)?.find(x=>x.arms.every(arm=>arm.every(i=>chosen.has(i))));assert(row,`Missing training registration: ${input.fold}/${cid}`);return row.id;});
  const check=portableWitnessCheck(live,new Set(selected));assert(check.valid);return {name:record.name,selected,verifiedCommonValues:check.witnesses.length};
 });
 models.push({fold:input.fold,file:input.file,model,trainingLifts});checks.push({file:input.file,registeredVariants:candidates.length,representedBasePlacements:liftLookup.size,trainingRecords:trainingLifts.length,verifiedCommonValues:trainingLifts.reduce((n,l)=>n+l.verifiedCommonValues,0)});console.log(JSON.stringify(checks.at(-1)));
}
writeFileSync(out,JSON.stringify({scope:'Finite registered model from geometry-only cloud proposals. No junction-state tables enter generation or compilation. Known fills only validate the frozen pool.',compiledHash:hash(compiledPath),portableHash:hash(portablePath),registrationHash:hash(registrationPath),alternativeHash:hash(alternativePath),sourceHash:hash(new URL(import.meta.url)),clouds,models,checks}),{flag:'wx'});
