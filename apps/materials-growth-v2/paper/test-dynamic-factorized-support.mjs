import assert from 'node:assert/strict';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
import {SupportOrderedFactorizedSearch} from './support-ordered-factorized-search.mjs';
import {InterleavedFactorizedSearch,diagonalPairs} from './interleaved-factorized-search.mjs';
import {RelationalEndpointSearch} from './relational-endpoint-search.mjs';
const relational=process.argv.includes('--relation'),choicesPerBlock=relational?3:4,radix=choicesPerBlock+1;
for(let a=0;a<9;a++)for(let b=0;b<9;b++){
 const left=Array.from({length:a},(_,i)=>2*i),right=Array.from({length:b},(_,i)=>3*i);
 const pairs=[...diagonalPairs(left,right)].map(JSON.stringify);
 assert.equal(new Set(pairs).size,a*b);assert.deepEqual(pairs.sort(),left.flatMap(i=>right.map(j=>JSON.stringify([i,j]))).sort());
}
let seed=19438,states=0,memberships=0,rollbacks=0,solutions=0,iteratorRollbacks=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
const snapshot=e=>JSON.stringify({p:[...e.points],g:[...e.graph].map(([p,v])=>[p,[...v].sort()]).sort(),d:e.blocks.map(b=>b.domain.snapshot()),o:[...e.owners],k:[...e.placed]});
for(let trial=0;trial<100;trial++){
 const points=['a','b','c'],model={capacity:2,required:points,blocks:[]};
 for(let i=0;i<5;i++){
  const a=points[random(3)],b=points.filter(p=>p!==a)[random(2)];
  model.blocks.push({id:String(i),inventory:String(random(4)),t:[{point:a,value:1},{point:b,value:1}],markPoints:[a,b],endpointChoices:[[random(3),random(3)],[random(3),random(3)]]});
 }
 const records=model.blocks.flatMap((b,i)=>b.endpointChoices.flatMap((cs,side)=>cs.map((_,j)=>[i,side,j])));
 const neighbors=records.map(([i,s,j])=>records.flatMap(([k,t,l],n)=>model.blocks[i].inventory!==model.blocks[k].inventory&&model.blocks[i].markPoints[s]===model.blocks[k].markPoints[t]&&model.blocks[i].endpointChoices[s][j]===model.blocks[k].endpointChoices[t][l]?[n]:[]));
 if(relational)model.allowedPairs=model.blocks.map((_,i)=>i%2?[[0,0],[1,0],[1,1]]:[[0,0],[0,1],[1,1]]);
 const ordered=process.argv.includes('--support-order'),interleaved=process.argv.includes('--interleaved'),Engine=relational?RelationalEndpointSearch:interleaved?InterleavedFactorizedSearch:ordered?SupportOrderedFactorizedSearch:DynamicFactorizedSupportSearch;
 const e=new Engine(model,{partnerIndex:ordered||process.argv.includes('--indexed')?{records,neighbors}:null}),all=[];
 for(const b of e.blocks)for(let left=0;left<2;left++)for(let right=0;right<2;right++)if(!relational||model.allowedPairs[b.index].some(([a,c])=>a===left&&c===right))all.push({id:e.candidateId(b.index,left,right),b,left,right,marks:new Map([[b.markPoints[0],b.endpointChoices[0][left]],[b.markPoints[1],b.endpointChoices[1][right]]])});
 function audit(){
  let live=new Set(all.filter(c=>!e.owners.has(c.b.inventory)&&c.b.t.every(t=>e.points.get(t.point).total+1<=2)&&[...c.marks].every(([p,v])=>e.points.get(p).marks.every(a=>a.value===v))).map(c=>c.id));
  let changed;
  do{changed=false;for(const c of all)if(live.has(c.id))for(const [p,v] of c.marks){
   if(e.points.get(p).total!==0)continue;
   if(!all.some(o=>live.has(o.id)&&o.b.inventory!==c.b.inventory&&o.marks.has(p)&&o.marks.get(p)===v)){live.delete(c.id);changed=true;break;}
  }}while(changed);
  for(const c of all){assert.equal(c.b.domain.has(c.left,c.right),live.has(c.id));memberships++;}
  for(const p of points){const expected=all.filter(c=>live.has(c.id)&&c.b.t.some(t=>t.point===p)).map(c=>c.id).sort();assert.deepEqual([...e.candidateIds(p)].sort(),e.points.get(p).total<2?expected:[]);}
  states++;
 }
 audit();const root=snapshot(e),stack=[];
 for(const point of points){
  const expected=[...e.candidateIds(point)],iterator=e.candidateIds(point),first=iterator.next();
  if(first.done)continue;
  e.apply(first.value);const next=e.candidateIds(point).next();if(!next.done)e.apply(next.value);
  e.undo(0);assert.equal(snapshot(e),root);assert.deepEqual([first.value,...iterator],expected);iteratorRollbacks++;audit();
 }
 for(let i=0;i<40;i++){
  if(stack.length&&random(3)===0){const frame=stack.pop();e.undo(frame.cp);assert.equal(snapshot(e),frame.before);rollbacks++;}
  else{const legal=all.filter(c=>c.b.domain.has(c.left,c.right));if(legal.length){const c=legal[random(legal.length)],before=snapshot(e),cp=e.apply(c.id);stack.push({before,cp});}}
  audit();
 }
 e.undo(0);assert.equal(snapshot(e),root);audit();
 // Independent exhaustive full fillings: absent or one of four decorations
 // per block. Replay each legal solution through dynamic propagation.
 let trialSolutions=0;
 for(let code=0;code<radix**5;code++){
  let n=code;const chosen=[],totals={a:0,b:0,c:0},marks=new Map(),owners=new Set();let legal=true;
  for(let i=0;i<5;i++){const v=n%radix;n=Math.floor(n/radix);if(!v)continue;const c=all[choicesPerBlock*i+v-1];chosen.push(c);if(owners.has(c.b.inventory))legal=false;owners.add(c.b.inventory);for(const t of c.b.t)totals[t.point]++;for(const [p,m] of c.marks){if(marks.has(p)&&marks.get(p)!==m)legal=false;marks.set(p,m);}}
  if(!legal||Object.values(totals).some(t=>t!==2))continue;
  solutions++;trialSolutions++;for(const c of chosen){assert(c.b.domain.has(c.left,c.right));e.apply(c.id);audit();}assert.equal(e.decision().kind,'complete');e.undo(0);assert.equal(snapshot(e),root);
 }
 let last;for(let step=0;step<10000;step++){last=e.advance();audit();if(['complete','exhausted','unknown'].includes(last.kind))break;}
 assert.equal(last.kind,trialSolutions?'complete':'exhausted');e.undo(0);assert.equal(snapshot(e),root);
}
assert(solutions>0);
console.log(JSON.stringify({models:100,relational,indexed:process.argv.includes('--indexed'),supportOrdered:process.argv.includes('--support-order'),interleaved:process.argv.includes('--interleaved'),states,memberships,rollbacks,iteratorRollbacks,fullSelections:100*radix**5,solutionsPreserved:solutions,dfsOutcomesMatch:true,scope:'Dynamic fixed-point domains vs explicit decorated candidates; scalar singleton marking model. Cloud/material integration remains separate.'}));
