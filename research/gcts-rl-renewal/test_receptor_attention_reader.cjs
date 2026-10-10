'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const Q=require(path.join(root,'receptor-attention.js')),data=JSON.parse(fs.readFileSync(path.join(root,'receptor-attention-reader-001.json'))),stats=Q.validate(data);
const copy=x=>JSON.parse(JSON.stringify(x)),reject=f=>assert.throws(f);let points=0,lines=0,events=0,updates=0,clocks=0;
for(const c of [...data.donors.map(d=>({...d,runs:{donor:d.result}})),...data.cases])for(const r of Object.values(c.runs)){
 if(!r.proof)continue;
 for(const field of ['occupancy','marks']){let bad=copy(r);if(field==='occupancy')bad.tiles[0][field][0][1]=11;else bad.tiles[0][field][0][1]='!';reject(()=>Q.check({...c,result:bad}));points++;}
 let bad=copy(r);bad.proof[0].formula=['bot'];reject(()=>Q.check({...c,result:bad}));lines++;
 for(const e of r.attention_events.filter(e=>e.items.length))for(const field of ['features','scores','probabilities','gradient','selected','chosen','point']){
  const b=copy(e);if(field==='features')b[field][0][0]++;else if(['scores','probabilities','gradient'].includes(field))b[field][0]++;else if(field==='selected')b[field]=(b[field]+1)%(b.items.length+1);else if(field==='chosen')b[field]=[[999,999,[]]];else b[field]=[999,0];
  if(field==='point'){const d=copy(data),target=d.cases.find(v=>v.spec.id===c.spec.id);if(!target)continue;target.runs[r===c.runs.attention?'attention':Object.keys(c.runs).find(k=>c.runs[k]===r)].attention_events.find(v=>v.id===e.id).point=[999,0];reject(()=>Q.validate(d));}
  else reject(()=>Q.event(c,r,b,data.library));events++;
 }
}
for(const e of data.training.episodes.slice(0,6))for(const field of ['reward','baseline_before','gradient','weights_after']){const d=copy(data),u=d.training.episodes[e.id].update;if(Array.isArray(u[field]))u[field][0]++;else u[field]++;reject(()=>Q.validate(d));updates++;}
for(const c of data.cases)for(const lane of data.lanes){const d=copy(data);d.cases.find(v=>v.spec.id===c.spec.id).timings[lane].median_seconds++;reject(()=>Q.validate(d));clocks++;}
console.log(JSON.stringify({...stats,point_mutations:points,source_mutations:lines,attention_mutations:events,update_mutations:updates,timing_mutations:clocks}));
