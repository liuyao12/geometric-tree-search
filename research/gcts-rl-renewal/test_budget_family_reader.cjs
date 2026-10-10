const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const dir=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const box={module:{exports:{}},crypto:crypto.webcrypto,TextEncoder};vm.createContext(box);
vm.runInContext(fs.readFileSync(path.join(dir,'budget-families.js'),'utf8'),box);
const F=box.module.exports,original=JSON.parse(fs.readFileSync(path.join(dir,'budget-families-reader-001.json'),'utf8'));
const clone=()=>JSON.parse(JSON.stringify(original));
(async()=>{
 const stats=await F.validate(original),rejected={};
 async function refuse(label,change){const d=clone();change(d);let failed=false;try{await F.validate(d);}catch(e){failed=true;}if(!failed)throw Error('Reader accepted corrupted '+label);rejected[label]=(rejected[label]||0)+1;}
 for(let i=0;i<original.cases.length;i++){
  await refuse('certificate_context',d=>d.cases[i].certificate.context_sha256='0'.repeat(64));
  await refuse('whole_root',d=>d.cases[i].runs.rl.root_marks.pop());
  await refuse('actual_capacity',d=>d.cases[i].runs.rl.tiles[0].occupancy[0][1]=11);
  if(original.cases[i].runs.rl.proof)await refuse('source_formula',d=>d.cases[i].runs.rl.proof.at(-1).formula=['bot']);
  const e=original.cases[i].runs.rl.attention_events.find(e=>e.items.length);
  if(e){
   await refuse('justified_feature',d=>d.cases[i].runs.rl.attention_events.find(x=>x.id===e.id).features[1][3]+=.2);
   await refuse('actual_score',d=>d.cases[i].runs.rl.attention_events.find(x=>x.id===e.id).scores[1]+=.2);
  }
 }
 for(const field of ['round','eligible','required'])await refuse('fixed_point_'+field,d=>{const t=d.cases[0].certificate;if(field==='round')t.rounds[0][t.target]=[];else if(field==='eligible')t.eligible_rules.pop();else t.required[t.target]++;});
 await refuse('distant_zero',d=>d.cases[0].runs.rl.tiles.find(t=>t.marks.some(([p])=>p[0]===-3000)).marks.find(([p])=>p[0]===-3000)[1]=1);
 await refuse('family_aggregate',d=>d.cases[0].runs.rl.hints[0].item.marks.find(([p])=>p[0]===-3000)[1]=1);
 await refuse('family_pattern',d=>d.library[0].pattern[0].kind='mp');
 await refuse('family_hierarchy',d=>d.library.find(t=>t.children.length).children[0].offsets[0]=999);
 for(const field of ['reward','gradient','weights'])await refuse('training_'+field,d=>{const e=d.training.episodes[0];if(field==='reward')e.update.reward+=.1;else if(field==='gradient')e.update.gradient[0]+=.1;else e.weights_before[0]=1;});
 for(const lane of original.lanes)await refuse('cold_median',d=>d.cases[0].timings[lane].median_seconds+=.01);
 await refuse('balanced_order',d=>d.cases[0].timings.rl.samples[0].order.reverse());
 await refuse('tree_binding',d=>d.cases[0].timings.rl.samples[0].semantic_sha256='0'.repeat(64));
 await refuse('preparation_cost',d=>d.first_use_rl_seconds+=1);
 console.log(JSON.stringify({...stats,mutations_rejected:rejected,total_mutations:Object.values(rejected).reduce((a,b)=>a+b,0)}));
})().catch(e=>{console.error(e.stack);process.exit(1);});
