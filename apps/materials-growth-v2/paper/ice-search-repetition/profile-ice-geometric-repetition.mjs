// Read-only search instrumentation: no cache-based pruning or ordering changes.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {gaussianPointClass} from './gaussian-point-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const [input,kernel,out]=process.argv.slice(2),data=JSON.parse(readFileSync(input));
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const {PointSearch}=await import(pathToFileURL(kernel));const results=[];
for(const row of data.models)for(const enabled of [false,true]){
 const model=row.model,geometries=new Map(),incident=new Map();
 for(const c of model.candidates){
  if(geometries.has(c.base))assert.deepEqual(geometries.get(c.base),c.t);else{
   geometries.set(c.base,c.t);for(const t of c.t){if(!incident.has(t.point))incident.set(t.point,[]);incident.get(t.point).push(c.base);}
  }
 }
 const Base=gaussianPointClass(linearFrontierClass(PointSearch),model,{enabled});
 const observed=new Map(),dead=new Map();let decisions=0;
 class Profile extends Base{
  decision(){
   const d=super.decision(),owners=[...this.fieldOwners].sort(),key=JSON.stringify(owners);decisions++;
   observed.set(key,(observed.get(key)||0)+1);
   if(d.kind==='dead'){
    // Independent geometric legality ignores all fields and branch preferences.
    const legal=(incident.get(d.point)||[]).filter(base=>!this.fieldOwners.has(base)&&geometries.get(base).every(t=>this.points.get(t.point).total+t.value<=model.capacity));
    if(!dead.has(key))dead.set(key,{owners,visits:0,geometricDeadVisits:0,markingDependentVisits:0,examples:[]});
    const r=dead.get(key);r.visits++;if(!legal.length)r.geometricDeadVisits++;else r.markingDependentVisits++;
    if(r.examples.length<2)r.examples.push({point:d.point,geometricallyLegalInventories:legal.length,selected:[...this.placed.keys()]});
   }return d;
  }
 }
 const e=new Profile(model),root=JSON.stringify(e.semanticState()),start=performance.now();let steps=0,last;
 while(steps<500){last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;}
 const seconds=(performance.now()-start)/1000;e.auditGraph();
 const deadRows=[...dead.values()];const r={id:row.id,enabled,steps,decisions,seconds,status:last.kind,uniqueGeometricSelectedSets:observed.size,repeatedGeometricSelectedSetVisits:decisions-observed.size,deadVisits:deadRows.reduce((a,r)=>a+r.visits,0),uniqueDeadGeometricSelectedSets:dead.size,geometricDeadVisits:deadRows.reduce((a,r)=>a+r.geometricDeadVisits,0),markingDependentDeadVisits:deadRows.reduce((a,r)=>a+r.markingDependentVisits,0),stats:{...e.stats},deadStates:deadRows};
 e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);r.rootRollback=true;results.push(r);console.log(JSON.stringify({...r,deadStates:deadRows.length}));
}
writeFileSync(out,JSON.stringify({sourceHash:sha(input),kernelHash:sha(kernel),codeHashes:Object.fromEntries(['profile-ice-geometric-repetition.mjs','gaussian-point-filter.mjs','linear-frontier-decision.mjs'].map(f=>[f,sha(new URL(f,import.meta.url))])),results,limits:'First 500 advances, instrumentation only. Repeated selected geometry is not proof of equivalent marked states: fields and search-stack exclusions may differ. Geometric dead classification independently ignores markings but still uses the same finite input pool. No pruning or speedup claim.'},null,2),{flag:'wx'});
