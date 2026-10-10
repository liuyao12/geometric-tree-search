'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const Q=require(path.join(root,'quantifier-families.js'));
const data=JSON.parse(fs.readFileSync(path.join(root,'quantifier-families-reader-001.json'))),stats=Q.validate(data),copy=x=>JSON.parse(JSON.stringify(x));
let points=0,source=0,contexts=0,queries=0,phases=0,timings=0;
const reject=fn=>assert.throws(fn);
for(const c of [...data.donors.map(d=>({...d,runs:{donor:d.result}})),...data.cases])for(const r of Object.values(c.runs)){
 if(!r.proof)continue;
 for(const tile of r.tiles){let bad=copy(r);bad.tiles.find(t=>t.key[0]===tile.key[0]).occupancy[0][1]=11;reject(()=>Q.check({...c,result:bad}));points++;bad=copy(r);bad.tiles.find(t=>t.key[0]===tile.key[0]).marks[0][1]='!';reject(()=>Q.check({...c,result:bad}));points++;}
 for(let j=0;j<r.proof.length;j++){const bad=copy(r);bad.proof[j].formula=['bot'];reject(()=>Q.check({...c,result:bad}));source++;}
 let bad=copy(r);bad.compact.request.theory.axioms['invented']=['bot'];reject(()=>Q.check({...c,result:bad}));contexts++;
 for(let j=0;j<r.timeline.length;j++)if(r.timeline[j].hint_in!==null){bad=copy(r);bad.timeline[j].entry_review.phase='invented';reject(()=>Q.trace(c,bad,data.library));phases++;}
 if(r.index){bad=copy(r);bad.index.metrics.query_cache_hits++;reject(()=>Q.index(c,bad));queries++;bad=copy(r);bad.index.queries[0].occurrences++;reject(()=>Q.index(c,bad));queries++;const node=Object.values(bad.index.nodes).find(n=>n.rows.length);node.rows[0][1]['invented']=['bot'];reject(()=>Q.index(c,bad));queries++;}
}
for(const c of data.cases)for(const lane of Object.keys(c.runs)){const bad=copy(data);bad.cases.find(x=>x.spec.id===c.spec.id).timings[lane].median_seconds++;reject(()=>Q.validate(bad));timings++;}
let bad=copy(data);bad.library.find(t=>t.level===2).children[0].offsets=[];reject(()=>Q.validate(bad));
const px=t=>['pred','P',[t]],r=(a,b)=>['pred','R',[a,b]];
const x=['var','x'],v=['var','v'],u=['all','x',['all','v',r(x,v)]];
assert.deepStrictEqual(Q.subst(u[2],'x',v),['all','fresh0',r(v,['var','fresh0'])]);
assert.notDeepStrictEqual(Q.normal(Q.subst(u[2],'x',v)),Q.normal(['all','v',r(v,v)]));
console.log(JSON.stringify({...stats,point_mutations:points,source_mutations:source,context_mutations:contexts,index_mutations:queries,lifetime_mutations:phases,timing_mutations:timings,hierarchy_mutations:1}));
