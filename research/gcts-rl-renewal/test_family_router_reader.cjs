'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=path.join(__dirname,'../../docs/research/gcts-rl-renewal'),M=require(path.join(dir,'family-router.js')),data=JSON.parse(fs.readFileSync(path.join(dir,'family-router-reader-001.json')));
const clone=v=>JSON.parse(JSON.stringify(v)),reject=fn=>assert.throws(fn),stats=M.validate(data);
const all=[...data.donors.map(c=>[c,c.result]),...data.cases.flatMap(c=>Object.values(c.runs).map(r=>[c,r])),...data.training.feedback.flatMap(c=>Object.values(c.runs).map(r=>[c,r]))];
let point=0,source=0,context=0,route=0,timing=0,updates=0;
for(const [c,r] of all)if(r.proof!==null){
 const a=clone(r);a.tiles[0].marks[0][1]='wrong';reject(()=>M.check({...c,result:a}));point++;
 const b=clone(r);b.proof[0].formula=['bot'];reject(()=>M.check({...c,result:b}));source++;
}
for(const [i,c] of data.training.feedback.entries()){
 const bad=clone(c);bad.context.features[0]+=1;const t={...data.training,feedback:data.training.feedback.map((x,j)=>i===j?bad:x)};reject(()=>M.training(t));context++;
 for(const lane of ['base','fixed']){const b=clone(c);b.timings[lane].samples[0].seconds=0;reject(()=>M.timing(b,lane,i,true));timing++;}
}
for(const [i,c] of data.cases.entries())for(const lane of ['router','zero']){
 for(const field of ['features','basis','score','selected','point','weights']){
  const bad=clone(c.runs[lane]);if(['features','basis','weights'].includes(field))bad.router_event[field][0]+=10;else if(field==='point')bad.router_event.point=[999,0];else bad.router_event[field]+=10;
  reject(()=>M.route(c,bad,data.training.policy,lane));route++;
 }
 for(const method of ['base','fixed','router','zero'])if(lane==='router'){const b=clone(c);b.timings[method].samples[0].semantic_sha256='wrong';reject(()=>M.timing(b,method,i));timing++;}
}
for(const field of ['score','probabilities','selected','expected_reward','weights_after']){
 const t=clone(data.training),u=t.policy.selection.candidates[0].updates[0];if(Array.isArray(u[field]))u[field][0]+=1;else u[field]+=1;
 reject(()=>M.training(t));updates++;
}
const t=clone(data.training);t.policy.selection.selected=3;reject(()=>M.training(t));updates++;
process.stdout.write(JSON.stringify({...stats,point_mutations:point,source_mutations:source,context_mutations:context,route_mutations:route,timing_mutations:timing,update_mutations:updates})+'\n');
