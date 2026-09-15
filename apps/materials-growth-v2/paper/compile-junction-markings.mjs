// Explicit point-value marking realization of the implicit junction model.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [compiledPath,junctionPath,alternativePath,kernel,dest,searchFolder]=process.argv.slice(2);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const compiled=JSON.parse(readFileSync(compiledPath)),junctions=JSON.parse(readFileSync(junctionPath)),alternatives=JSON.parse(readFileSync(alternativePath));
assert.equal(junctions.inputHash,compiled.inputHash);assert.equal(junctions.learningHash,compiled.learningHash);assert.equal(junctions.alternativeHash,hash(alternativePath));
const {verify}=await import(pathToFileURL(kernel));mkdirSync(dest);const checks=[];
for(const input of compiled.models){
 const nodes=junctions.folds[input.fold].nodes,byPoint=new Map(nodes.map(n=>[String(n.point),n]));
 const candidates=[],byKey=new Map();
 for(const base of input.candidates){
  const domains=base.t.filter(x=>byPoint.has(x.point)).map(x=>({point:x.point,choices:byPoint.get(x.point).states.flatMap((s,i)=>s.candidates.includes(Number(base.id))?[i]:[])}));
  function emit(index,marks){
   if(index<domains.length){const n=domains[index];for(const value of n.choices)emit(index+1,[...marks,{point:n.point,channel:'junction',lo:value,hi:value}]);return;}
   const key=JSON.stringify([base.id,marks.map(m=>[m.point,m.lo])]),id=String(candidates.length).padStart(8,'0');assert(!byKey.has(key));byKey.set(key,id);
   candidates.push({id,base:base.id,t:base.t,m:[...base.m.filter(m=>m.channel==='0'),...marks]});
  }
  emit(0,[]);
 }
 assert.equal(candidates.length,junctions.folds[input.fold].expandedCandidateCount);
 const model={capacity:input.capacity,required:input.required,candidates},byId=new Map(candidates.map(c=>[c.id,c]));
 const covers=[{name:'original',selected:input.trainingSelected},...alternatives.runs.filter(r=>r.fold===input.fold).map(r=>({name:`alternative-${r.seed}`,selected:r.selected.map(i=>String(i).padStart(6,'0'))}))];
 const searchPath=searchFolder&&`${searchFolder}/${input.fold}-true.json`;
 if(searchPath&&existsSync(searchPath)){const run=JSON.parse(readFileSync(searchPath));if(run.result.status==='exact finite point-cover witness')covers.push({name:'reference-search-witness',selected:run.result.selected});}
 const lifted=[];
 for(const cover of covers){
  const chosen=new Set(cover.selected.map(Number)),labels=new Map();
  for(const n of nodes){
   const actual=n.incident.map(e=>e.candidate).filter(id=>chosen.has(id)).sort((a,b)=>a-b);
   const label=n.states.findIndex(s=>JSON.stringify([...s.candidates].sort((a,b)=>a-b))===JSON.stringify(actual));assert(label>=0);labels.set(String(n.point),label);
  }
  const ids=cover.selected.map(id=>{
   const base=input.candidates[Number(id)];assert.equal(base.id,id);
   const key=JSON.stringify([id,base.t.filter(x=>labels.has(x.point)).map(x=>[x.point,labels.get(x.point)])]);assert(byKey.has(key));return byKey.get(key);
  });
  // Membership in the full expanded model is checked above. Pass just these
  // members to the kernel verifier to avoid its linear candidate lookup cost.
  const selectedModel={...model,candidates:ids.map(id=>byId.get(id))};
  assert.equal(new Set(selectedModel.candidates.map(c=>c.base)).size,ids.length);
  assert(verify(selectedModel,ids).complete);lifted.push({name:cover.name,selected:ids.length,complete:true});
 }
 writeFileSync(`${dest}/${input.fold}.json`,JSON.stringify({model}),{flag:'wx'});
 checks.push({file:input.file,baseCandidates:input.candidates.length,markedVariants:candidates.length,lifted});
}
writeFileSync(`${dest}/check.json`,JSON.stringify({scope:'Explicit scalar junction labels; all recorded fillings lifted and checked by the native point-value verifier.',junctionHash:hash(junctionPath),kernelHash:hash(kernel),checks},null,2),{flag:'wx'});
console.log(JSON.stringify(checks.map(c=>({file:c.file,markedVariants:c.markedVariants,verifiedLifts:c.lifted.length}))));
