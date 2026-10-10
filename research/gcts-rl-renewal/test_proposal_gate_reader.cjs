'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const doc=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal'),G=require(path.join(doc,'proposal-gate.js'));
const data=JSON.parse(fs.readFileSync(path.join(doc,'proposal-gate-reader-001.json'))),stats=G.validate(data),copy=x=>structuredClone(x);
let points=0,source=0,contexts=0,queries=0,lifetimes=0,gates=0,timings=0,updates=0;
const reject=fn=>assert.throws(fn);
for(const c of [...data.donors.map(d=>({...d,runs:{donor:d.result}})),...data.cases])for(const r of Object.values(c.runs)){
 if(!r.proof)continue;
 for(const tile of r.tiles){let bad=copy(r);bad.tiles.find(t=>t.key[0]===tile.key[0]).occupancy[0][1]=11;reject(()=>G.check({...c,result:bad}));points++;bad=copy(r);bad.tiles.find(t=>t.key[0]===tile.key[0]).marks[0][1]='!';reject(()=>G.check({...c,result:bad}));points++;}
 for(let j=0;j<r.proof.length;j++){const bad=copy(r);bad.proof[j].formula=['bot'];reject(()=>G.check({...c,result:bad}));source++;}
 let bad=copy(r);bad.compact.request.theory.axioms.invented=['bot'];reject(()=>G.check({...c,result:bad}));contexts++;
 for(let j=0;j<r.timeline.length;j++){
  if(r.timeline[j].hint_in!==null){bad=copy(r);bad.timeline[j].entry_review.phase='invented';reject(()=>G.trace(c,bad,data.library));lifetimes++;}
  if(r.timeline[j].gate_event){bad=copy(r);bad.timeline[j].gate_event.features[2]+=1;reject(()=>G.leaf(c,bad));gates++;bad=copy(r);bad.timeline[j].gate_event.selected=1-bad.timeline[j].gate_event.selected;reject(()=>G.leaf(c,bad));gates++;}
 }
 if(r.index){bad=copy(r);bad.index.metrics.query_cache_hits++;reject(()=>G.index(c,bad));queries++;bad=copy(r);bad.index.queries[0].occurrences++;reject(()=>G.index(c,bad));queries++;const node=Object.values(bad.index.nodes).find(n=>n.rows.length);node.rows[0][1].invented=['bot'];reject(()=>G.index(c,bad));queries++;}
}
for(const c of data.cases)for(const lane of Object.keys(c.runs)){const bad=copy(c);bad.timings[lane].median_seconds++;reject(()=>G.timing(bad,lane));timings++;}
for(const field of ['reward','observed_total_seconds','baseline_before']){const bad=copy(data.training);bad.episodes[0].update[field]+=1;reject(()=>G.training(bad));updates++;}
for(const field of ['score','draw','selected']){const bad=copy(data.training);bad.episodes[0].events[0][field]+=1;reject(()=>G.training(bad));updates++;}
let bad=copy(data);bad.library.find(t=>t.level===2).children[0].offsets=[];reject(()=>G.validate(bad));
const gated=data.cases.find(c=>c.runs.gate.timeline.some(row=>row.gate_event)),changed=copy(gated.runs.gate);changed.timeline.find(row=>row.gate_event).gate_event=null;reject(()=>G.leaf(gated,changed));gates++;
console.log(JSON.stringify({...stats,point_mutations:points,source_mutations:source,context_mutations:contexts,index_mutations:queries,lifetime_mutations:lifetimes,gate_mutations:gates,timing_mutations:timings,update_mutations:updates,hierarchy_mutations:1}));
