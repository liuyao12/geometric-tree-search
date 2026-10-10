'use strict';
/* Bind each readable cell to the actual atomic tile, or the classical assignment. */
function readClusterProof(record){
 const readBase=typeof module!=='undefined'?require('./induction-tile-reading.js').readInductionTiles:readInductionTiles;
 const steps=readBase(record),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),need=(v,s)=>{if(!v)throw Error(s);};
 const sorted=entries=>entries.slice().sort((a,b)=>a[0][0]-b[0][0]||a[0][1]-b[0][1]);
 need(same(record.initial_marks,sorted([[[2*(record.problem.length-1),1],record.target_id],...Array.from({length:record.problem.length},(_,j)=>[[2*j,4],0])])),'Actual target and certified resource boundary');
 const assigned=new Map(record.initial_marks.map(([p,v])=>[p.join(','),v]));
 steps.forEach(t=>t.marks.forEach(([p,v])=>{const k=p.join(',');need(!assigned.has(k)||same(assigned.get(k),v),'All proof and fixed boundary markings agree');assigned.set(k,v);}));
 if(record.lane.startsWith('csp')){
  need(record.atomic_tiles.length===0&&steps.every(t=>t.parent_candidate===null&&t.search_step===null&&t.marks.every(([p])=>p[1]!==2)),'Classical assignment has no atomic point-placement chronology');
  record.classical_proposals.forEach(p=>p.members.forEach(([slot,rid,refs])=>{const t=steps.find(t=>t.slot===slot);need(t&&t.rule_id===rid&&same(t.refs,refs),'Classical proposal matches the accepted witness');}));
 }else{
  need(new Set(record.atomic_tiles.map(t=>t.candidate)).size===record.atomic_tiles.length,'Distinct selected atomic tiles');
  const slots=new Set();
  record.atomic_tiles.forEach((tile,i)=>{
   need(tile.search_step===i+1,'Actual atomic placement order');const weights=new Map(),marks=new Map();
   tile.members.forEach(([slot,rid,refs])=>{
    need(!slots.has(slot),'Disjoint atomic occupancy');slots.add(slot);const t=steps.find(t=>t.slot===slot);
    need(t&&t.parent_candidate===tile.candidate&&t.search_step===tile.search_step&&t.rule_id===rid&&same(t.refs,refs),'Exact constituent descriptor');
    t.weights.forEach(([p,v])=>{const key=p.join(',');if(!weights.has(key))weights.set(key,[p,0]);weights.get(key)[1]+=v;});
    t.marks.forEach(([p,v])=>{const key=p.join(',');need(!marks.has(key)||same(marks.get(key)[1],v),'Compatible constituent values');if(p[1]===2)need(v===tile.candidate,'Actual atomic ownership');marks.set(key,[p,v]);});
   });
   need(same(sorted([...weights.values()]),tile.weights)&&same(sorted([...marks.values()]),tile.marks),'Actual atomic point functions equal the constituent union');
  });
  need(slots.size===record.problem.length,'Complete actual atomic proof strip');
 }
 return steps;
}
if(typeof module!=='undefined')module.exports={readClusterProof};
