'use strict';
const fs=require('fs'),path=require('path'),R=require('../../docs/research/gcts-rl-renewal/resumable-clusters.js'),K=require('../../docs/research/gcts-rl-renewal/quantified-receptors.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../../docs/research/gcts-rl-renewal/resumable-clusters-reader-001.json'))),stats={...R.validate(data),kernel_certificates:0,point_mutations:0,formula_mutations:0,context_mutations:0,lifetime_mutations:0,hierarchy_mutations:0};
function reject(fn,key){let caught=false;try{fn();}catch(e){caught=true;}if(!caught)throw Error('Corrupted reader accepted');stats[key]++;}
for(const c of data.donors.map(c=>({...c,runs:{donor:c.result}})).concat(data.cases))for(const r of Object.values(c.runs)){if(r.proof===null)continue;const record={...c,result:r};K.checkRequest(r.compact.request);stats.kernel_certificates++;
 for(const t of r.tiles){const old=t.occupancy[0][1];t.occupancy[0][1]=11;reject(()=>R.check(record),'point_mutations');t.occupancy[0][1]=old;
  const layers=new Map();for(const m of t.marks){const layer=m[0][1]===-2?'flow':m[0][0]===-1000?'scope':m[0][1]===1?'context':m[0][0]===2*t.key[0]?'output':'premise';if(!layers.has(layer))layers.set(layer,m);}
  for(const m of layers.values()){const old=m[1];m[1]='!';reject(()=>R.check(record),'point_mutations');m[1]=old;}
 }
 for(const cmd of r.compact.request.proof){const old=cmd.formula;cmd.formula=['bot'];reject(()=>K.checkRequest(r.compact.request),'formula_mutations');cmd.formula=old;}
 const p=r.compact,old=p.request.theory;p.request.theory={...old,axioms:{...old.axioms,cheat:['imp',['bot'],['bot']]}};reject(()=>R.check(record),'context_mutations');p.request.theory=old;
 for(const b of p.source_bindings){const k=String(b.last),v=p.conditional_map[k];p.conditional_map[k]=99999;reject(()=>R.check(record),'context_mutations');p.conditional_map[k]=v;}
 if(r.timeline.length){for(const t of r.timeline){const old=t.step;t.step=-1;reject(()=>R.trace(c,r,data.library),'lifetime_mutations');t.step=old;}
  for(const t of r.timeline.filter(t=>t.phase!=='none')){const old=t.phase;t.phase='none';reject(()=>R.trace(c,r,data.library),'lifetime_mutations');t.phase=old;if(t.pending.length){const old=t.pending;t.pending=[];reject(()=>R.trace(c,r,data.library),'lifetime_mutations');t.pending=old;}}
  for(const h of r.hints){const m=h.item.marks[0],old=m[1];m[1]='!';reject(()=>R.trace(c,r,data.library),'lifetime_mutations');m[1]=old;}
  if(r.solution_hints.length){const old=r.solution_hints;r.solution_hints=[];reject(()=>R.trace(c,r,data.library),'lifetime_mutations');r.solution_hints=old;}
 }
}
for(const t of data.library){const old=t.level;t.level=99;reject(()=>R.library(data),'hierarchy_mutations');t.level=old;
 for(const child of t.children){const old=child.offsets;child.offsets=[0];reject(()=>R.library(data),'hierarchy_mutations');child.offsets=old;const id=child.hint_id;child.hint_id=9999;reject(()=>R.library(data),'hierarchy_mutations');child.hint_id=id;}
}
process.stdout.write(JSON.stringify(stats)+'\n');
