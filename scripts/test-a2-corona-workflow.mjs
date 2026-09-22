import fs from 'node:fs';
import assert from 'node:assert/strict';
import {workflowModel,learningProblem,fitSupport,compactSupport} from './experiment-a2-corona-workflow.mjs';
import {enumerateCoronas,verifyCoronaPatch} from './experiment-a2-corona-consensus.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
const dir=process.argv[2]??'/tmp/a2-corona-workflow';
// A free intermediary must BREAK the equality path, rather than merely hide
// its old value. Signed odd cycles force zero only while their edges survive.
const synthetic={domain:[0,1,2].map(component=>({tile:'test',point:[0,0,0],component})),equalities:[[0,1,1],[1,2,1]],pairs:[{positive:false,contacts:[[0,2,1]]}]};
assert.equal(fitSupport(synthetic,[true,true,true]).blocked,0);
assert.equal(fitSupport(synthetic,[true,false,true]).blocked,1);
assert.equal(fitSupport({...synthetic,equalities:[[0,0,-1]],pairs:[]},[true,false,false]).values[0],0);
// Independent map-based one-corona exhaustive search. Lexical obligations,
// freshly enumerated candidates, and no incremental graph or generation data.
function independentOne(model){
 const root={oi:0,translation:[0,0,0]},core=model.orientations[0].cells.map(c=>c.pos.join()).sort(),seen=new Set(),found=new Set();
 const id=p=>`${p.oi}:${p.translation}`,patchKey=p=>p.map(id).sort().join(';');
 function visit(patch,totals){const key=patchKey(patch);if(seen.has(key))return;seen.add(key);const at=core.find(k=>(totals.get(k)??0)<12);if(at===undefined){if(verifyGrowth(model,patch).ok)found.add(key);return;}
  const point=at.split(',').map(Number),used=new Set(patch.map(id)),tried=new Set();
  for(let oi=0;oi<model.orientations.length;oi++)for(const a of model.orientations[oi].cells){const translation=point.map((v,i)=>v-a.pos[i]),p={oi,translation},token=id(p);if(used.has(token)||tried.has(token))continue;tried.add(token);const next=new Map(totals);let ok=true;
   for(const c of model.orientations[oi].cells){const k=c.pos.map((v,i)=>v+translation[i]).join(),n=(next.get(k)??0)+c.weight;if(n>12){ok=false;break;}next.set(k,n);}if(ok)visit([...patch,p],next);
  }
 }
 visit([root],new Map(model.orientations[0].cells.map(c=>[c.pos.join(),c.weight])));return found;
}
// Independent full/compact compatibility comparison over every relative
// support alignment, including pairs whose t-supports do not touch.
function checkReduction(tile,full,compact){
 const a=workflowModel(tile,full),b=workflowModel(tile,compact),root=new Map(a.orientations[0].marks.map(e=>[`${e.pos}|${e.component}`,e.value])),small=new Map(b.orientations[0].marks.map(e=>[`${e.pos}|${e.component}`,e.value])),totals=new Map(a.orientations[0].cells.map(e=>[e.pos.join(),e.weight]));
 const rejected=(left,right,t)=>right.some(e=>{const k=`${e.pos.map((v,i)=>v+t[i])}|${e.component}`;return left.has(k)&&left.get(k)!==e.value;});
 for(let oi=0;oi<a.orientations.length;oi++){
  const shifts=new Set();for(const l of a.orientations[0].marks)for(const r of a.orientations[oi].marks)if(l.component===r.component)shifts.add(l.pos.map((v,i)=>v-r.pos[i]).join());
  for(const key of shifts){if(oi===0&&key==='0,0,0')continue;const t=key.split(',').map(Number);if(a.orientations[oi].cells.some(e=>(totals.get(e.pos.map((v,i)=>v+t[i]).join())??0)+e.weight>12))continue;
   assert.equal(rejected(root,a.orientations[oi].marks,t),rejected(small,b.orientations[oi].marks,t));
  }
 }
}
for(const tile of ['turtle','hat']){
 const c=JSON.parse(fs.readFileSync(`${dir}/${tile}-unmarked-c1.json`)),model=workflowModel(tile),independent=independentOne(model),keys=new Set(c.patches.map(p=>p.map(p=>`${p.oi}:${p.translation}`).sort().join(';')));
 assert.ok(c.complete);assert.deepEqual(keys,independent);const problem=learningProblem(tile,c),family=JSON.parse(fs.readFileSync(`${dir}/${tile}-family.json`));
 assert.equal(new Set(family.models.map(m=>m.signature)).size,family.models.length);
 for(const [i,m]of family.models.entries()){
  const fresh=fitSupport(problem,m.active);assert.deepEqual(fresh.support,m.support);assert.equal(fresh.blocked,m.blocked);
  checkReduction(tile,m.support,compactSupport(tile,m.support));
  for(const p of c.patches)assert.ok(problem.learner.verifyPatch(p.map(problem.spec),m.support).compatible);
  for(const radius of [1,2,3]){
   const file=`${dir}/${tile}-m${i}-c${radius}.json`;if(!fs.existsSync(file))continue;const r=JSON.parse(fs.readFileSync(file));if(!r.complete)continue;
   const input=workflowModel(tile,r.inputSupport);let common=null;
   for(const patch of r.patches){assert.ok(verifyCoronaPatch(input,patch,radius).ok);const section=new Map();for(const p of patch)for(const e of input.orientations[p.oi].marks){const k=`${e.pos.map((v,j)=>v+p.translation[j])}|${e.component}`;if(section.has(k))assert.ok(section.get(k)===e.value);section.set(k,e.value===0?0:e.value);}
    if(common===null)common=section;else for(const[k,v]of common)if(!section.has(k)||section.get(k)!==v)common.delete(k);
   }
   assert.deepEqual([...(common??[])].sort(),r.support.map(e=>[`${e.point}|${e.component}`,e.value===0?0:e.value]).sort());
   if(r.solutions){assert.deepEqual(compactSupport(tile,r.support),r.compactSupport);checkReduction(tile,r.support,r.compactSupport);}
   console.log(`${tile} m${i} c${radius}: replayed ${r.solutions} coronas and ${r.commonValues} common values.`);
  }
 }
 console.log(`${tile}: independent exhaustive one-corona catalogue ${c.solutions}; every learned candidate accepts every initial corona.`);
}
console.log('PASS complete initial catalogues, individual free values, distinct learned restrictions, signed overlap replay and complete-stage intersections.');
