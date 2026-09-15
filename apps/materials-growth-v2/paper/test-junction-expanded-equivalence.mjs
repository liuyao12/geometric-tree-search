// Independent exhaustive comparison of local junction tables with scalar
// marking variants. Includes a cyclic instance with several allowed fillings.
import assert from 'node:assert/strict';
const points=['a','b','c','d'],base=[];
for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)base.push({id:String(base.length),t:[{point:points[i],value:1},{point:points[j],value:1}]});
const nodes=points.map(point=>{
 const incident=base.filter(c=>c.t.some(x=>x.point===point)).map(c=>c.id),states=[];
 for(let i=0;i<incident.length;i++)for(let j=i+1;j<incident.length;j++)states.push([incident[i],incident[j]]);
 return {point,incident,states};
});
let stateCases=0,leafChecks=0;
for(const restricted of [false,true]){
 const tables=nodes.map((n,i)=>({...n,states:restricted&&i===0?n.states.slice(0,1):n.states}));
 const expected=new Set();
 for(let mask=0;mask<64;mask++){
  const chosen=base.filter((_,i)=>mask&(1<<i)).map(c=>c.id);
  if(tables.every(n=>n.states.some(s=>JSON.stringify(s)===JSON.stringify(chosen.filter(id=>n.incident.includes(id))))))expected.add(JSON.stringify(chosen));
 }
 const expanded=[];
 for(const c of base){
  const touched=tables.filter(n=>n.incident.includes(c.id));
  const choices=touched.map(n=>n.states.flatMap((s,i)=>s.includes(c.id)?[i]:[]));
  for(const i of choices[0])for(const k of choices[1])expanded.push({...c,m:[[touched[0].point,i],[touched[1].point,k]]});
 }
 const found=new Set(),totals=Object.fromEntries(points.map(p=>[p,0])),marks=new Map(),chosen=[];
 function visit(index){
  if(index===expanded.length){leafChecks++;
   if(Object.values(totals).every(t=>t===2)){
    assert.equal(new Set(chosen).size,chosen.length,'Marking variants permitted duplicate base placement');
    found.add(JSON.stringify([...chosen].sort()));
   }return;
  }
  visit(index+1);const c=expanded[index];
  if(c.t.some(x=>totals[x.point]+x.value>2)||c.m.some(([p,m])=>marks.has(p)&&marks.get(p)!==m))return;
  const old=new Map(marks);for(const x of c.t)totals[x.point]+=x.value;for(const [p,m] of c.m)marks.set(p,m);chosen.push(c.id);
  visit(index+1);chosen.pop();for(const x of c.t)totals[x.point]-=x.value;marks.clear();for(const [p,m] of old)marks.set(p,m);
 }
 visit(0);assert.deepEqual([...found].sort(),[...expected].sort());assert(found.size>0);stateCases++;
}
console.log(JSON.stringify({stateCases,expandedLeafChecks:leafChecks,projectedSolutionSetsEqual:true,noDuplicateBasePlacements:true}));
