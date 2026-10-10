const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const dir=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');const box={module:{exports:{}},crypto:crypto.webcrypto,TextEncoder};vm.createContext(box);vm.runInContext(fs.readFileSync(path.join(dir,'dependency-budget.js'),'utf8'),box);const D=box.module.exports;
const original=JSON.parse(fs.readFileSync(path.join(dir,'dependency-budget-reader-001.json'),'utf8'));
const clone=()=>JSON.parse(JSON.stringify(original));
(async()=>{const stats=await D.validate(original);let certificate=0,point=0,source=0,timing=0,rejection=0;
 async function refuse(fn){let failed=false;try{await fn();}catch(e){failed=true;}if(!failed)throw Error('Reader accepted corrupted record');}
 for(let i=0;i<original.cases.length;i++){
  for(const kind of ['context','round','eligible','required']){const d=clone(),t=d.cases[i].certificate;if(kind==='context')t.context_sha256='0'.repeat(64);else if(kind==='round')t.rounds[0][t.target]=[];else if(kind==='eligible')t.eligible_rules.pop();else t.required[t.target]++;await refuse(()=>D.validate(d));certificate++;}
  for(const lane of original.lanes){const d=clone();d.cases[i].timings[lane].median_seconds+=.01;await refuse(()=>D.validate(d));timing++;
   if(original.cases[i].runs[lane].proof){for(const kind of ['capacity','word','budget']){const d=clone(),r=d.cases[i].runs[lane];if(kind==='capacity')r.tiles[0].occupancy[0][1]=11;else if(kind==='word')r.tiles[0].marks.find(v=>v[0][0]!==-3000)[1]='!';else if(lane==='budget')r.tiles.find(t=>t.marks.some(v=>v[0][0]===-3000)).marks.find(v=>v[0][0]===-3000)[1]=1;else r.root_marks.push([[-3000,0],1]);await refuse(()=>D.validate(d));point++;}const d=clone();d.cases[i].runs[lane].proof.at(-1).formula=['bot'];await refuse(()=>D.validate(d));source++;}
  }
  for(const kind of ['original','marked','conflict']){const d=clone(),x=d.cases[i].rejection;if(kind==='original')x.original.occupancy[0][1]=11;else if(kind==='marked')x.marked.marks.find(v=>v[0][0]===-3000)[1]=0;else x.conflicts=[];await refuse(()=>D.validate(d));rejection++;}
 }
 console.log(JSON.stringify({...stats,certificate_mutations:certificate,point_mutations:point,source_mutations:source,timing_mutations:timing,rejection_mutations:rejection}));
})().catch(e=>{console.error(e.stack);process.exit(1);});
