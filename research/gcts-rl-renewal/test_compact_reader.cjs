'use strict';
const fs=require('fs'),path=require('path'),R=require('../../docs/research/gcts-rl-renewal/compact-contexts.js'),K=require('../../docs/research/gcts-rl-renewal/quantified-receptors.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../../docs/research/gcts-rl-renewal/compact-contexts-reader-001.json'))),stats={...R.validate(data),kernel_certificates:0,point_mutations:0,formula_mutations:0,context_mutations:0};
function reject(fn,key){let caught=false;try{fn();}catch(e){caught=true;}if(!caught)throw Error('Corrupted reader accepted');stats[key]++;}
for(const c of data.cases){if(c.result.proof===null)continue;K.checkRequest(c.result.compact.request);stats.kernel_certificates++;
 for(const t of c.result.tiles){const old=t.occupancy[0][1];t.occupancy[0][1]=11;reject(()=>R.check(c),'point_mutations');t.occupancy[0][1]=old;
  const selected=new Map();for(const m of t.marks){const layer=m[0][1]===-2?'flow':m[0][0]===-1000?'scope':m[0][1]===1?'context':m[0][0]===2*t.key[0]?'output':'premise';if(!selected.has(layer))selected.set(layer,m);}
  for(const m of selected.values()){const old=m[1];m[1]='!';reject(()=>R.check(c),'point_mutations');m[1]=old;}
 }
 for(const cmd of c.result.compact.request.proof){const old=cmd.formula;cmd.formula=['bot'];reject(()=>K.checkRequest(c.result.compact.request),'formula_mutations');cmd.formula=old;}
 const p=c.result.compact,old=p.request.theory;p.request.theory={...old,axioms:{...old.axioms,cheat:['imp',['bot'],['bot']]}};reject(()=>R.check(c),'context_mutations');p.request.theory=old;
 for(const b of p.source_bindings){const k=String(b.last),v=p.conditional_map[k];p.conditional_map[k]=99999;reject(()=>R.check(c),'context_mutations');p.conditional_map[k]=v;}
}
process.stdout.write(JSON.stringify(stats)+'\n');
