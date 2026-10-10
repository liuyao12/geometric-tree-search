'use strict';
const fs=require('fs'),path=require('path'),R=require('../../docs/research/gcts-rl-renewal/adaptive-clusters.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../../docs/research/gcts-rl-renewal/adaptive-clusters-reader-001.json'))),stats={...R.validate(data),point_mutations:0,row_mutations:0,cluster_mutations:0};
function rejects(fn,counter){let bad=false;try{fn();}catch(e){bad=true;}if(!bad)throw Error('Corrupted record accepted');stats[counter]++;}
for(const c of data.cases){for(const r of Object.values(c.runs)){if(!r.proof)continue;
 for(const tile of r.tiles){for(const m of tile.marks){const old=m[1];m[1]=typeof old==='number'?1-old:'!';rejects(()=>R.proof(c,r),'point_mutations');m[1]=old;}const old=tile.occupancy[0][1];tile.occupancy[0][1]=11;rejects(()=>R.proof(c,r),'point_mutations');tile.occupancy[0][1]=old;}
 for(const row of r.proof){const old=row.formula;row.formula=['bot'];rejects(()=>R.proof(c,r),'row_mutations');row.formula=old;const ref=row.refs[0];row.refs[0]=c.spec.bound+10;rejects(()=>R.proof(c,r),'row_mutations');row.refs[0]=ref;}
 for(const tr of r.solution_transactions){const t=tr.item;
  for(const m of t.marks){const old=m[1];m[1]=typeof old==='number'?1-old:'!';rejects(()=>R.cluster(c,r,t,data.library),'cluster_mutations');m[1]=old;}
  for(const m of t.occupancy){const old=m[1];m[1]=11;rejects(()=>R.cluster(c,r,t,data.library),'cluster_mutations');m[1]=old;}
  for(const k of Object.keys(t.bindings)){const old=t.bindings[k];t.bindings[k]=['bot'];rejects(()=>R.cluster(c,r,t,data.library),'cluster_mutations');t.bindings[k]=old;}
 }
}}
process.stdout.write(JSON.stringify(stats)+'\n');
