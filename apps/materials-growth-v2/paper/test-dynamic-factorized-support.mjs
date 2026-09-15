import assert from 'node:assert/strict';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
let seed=19438,states=0,memberships=0,rollbacks=0,solutions=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
const snapshot=e=>JSON.stringify({p:[...e.points],g:[...e.graph].map(([p,v])=>[p,[...v].sort()]).sort(),d:e.blocks.map(b=>b.domain.snapshot()),o:[...e.owners],k:[...e.placed]});
for(let trial=0;trial<100;trial++){
 const points=['a','b','c'],model={capacity:2,required:points,blocks:[]};
 for(let i=0;i<5;i++){
  const a=points[random(3)],b=points.filter(p=>p!==a)[random(2)];
  model.blocks.push({id:String(i),inventory:String(random(4)),t:[{point:a,value:1},{point:b,value:1}],markPoints:[a,b],endpointChoices:[[random(3),random(3)],[random(3),random(3)]]});
 }
 const e=new DynamicFactorizedSupportSearch(model),all=[];
 for(const b of e.blocks)for(let left=0;left<2;left++)for(let right=0;right<2;right++)all.push({id:e.candidateId(b.index,left,right),b,left,right,marks:new Map([[b.markPoints[0],b.endpointChoices[0][left]],[b.markPoints[1],b.endpointChoices[1][right]]])});
 function audit(){
  let live=new Set(all.filter(c=>!e.owners.has(c.b.inventory)&&c.b.t.every(t=>e.points.get(t.point).total+1<=2)&&[...c.marks].every(([p,v])=>e.points.get(p).marks.every(a=>a.value===v))).map(c=>c.id));
  let changed;
  do{changed=false;for(const c of all)if(live.has(c.id))for(const [p,v] of c.marks){
   if(e.points.get(p).total!==0)continue;
   if(!all.some(o=>live.has(o.id)&&o.b.inventory!==c.b.inventory&&o.marks.has(p)&&o.marks.get(p)===v)){live.delete(c.id);changed=true;break;}
  }}while(changed);
  for(const c of all){assert.equal(c.b.domain.has(c.left,c.right),live.has(c.id));memberships++;}
  for(const p of points){const expected=all.filter(c=>live.has(c.id)&&c.b.t.some(t=>t.point===p)).map(c=>c.id).sort();assert.deepEqual([...e.candidateIds(p)],e.points.get(p).total<2?expected:[]);}
  states++;
 }
 audit();const root=snapshot(e),stack=[];
 for(let i=0;i<40;i++){
  if(stack.length&&random(3)===0){const frame=stack.pop();e.undo(frame.cp);assert.equal(snapshot(e),frame.before);rollbacks++;}
  else{const legal=all.filter(c=>c.b.domain.has(c.left,c.right));if(legal.length){const c=legal[random(legal.length)],before=snapshot(e),cp=e.apply(c.id);stack.push({before,cp});}}
  audit();
 }
 e.undo(0);assert.equal(snapshot(e),root);audit();
 // Independent exhaustive full fillings: absent or one of four decorations
 // per block. Replay each legal solution through dynamic propagation.
 for(let code=0;code<3125;code++){
  let n=code;const chosen=[],totals={a:0,b:0,c:0},marks=new Map(),owners=new Set();let legal=true;
  for(let i=0;i<5;i++){const v=n%5;n=Math.floor(n/5);if(!v)continue;const c=all[4*i+v-1];chosen.push(c);if(owners.has(c.b.inventory))legal=false;owners.add(c.b.inventory);for(const t of c.b.t)totals[t.point]++;for(const [p,m] of c.marks){if(marks.has(p)&&marks.get(p)!==m)legal=false;marks.set(p,m);}}
  if(!legal||Object.values(totals).some(t=>t!==2))continue;
  solutions++;for(const c of chosen){assert(c.b.domain.has(c.left,c.right));e.apply(c.id);audit();}assert.equal(e.decision().kind,'complete');e.undo(0);assert.equal(snapshot(e),root);
 }
}
assert(solutions>0);
console.log(JSON.stringify({models:100,states,memberships,rollbacks,fullSelections:312500,solutionsPreserved:solutions,scope:'Dynamic fixed-point domains vs explicit decorated candidates; scalar singleton marking model. Cloud/material integration remains separate.'}));
