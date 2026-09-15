// Implicit junction-label choices on a fixed finite point model. A local state
// lists the complete incident base placements at one point. It is equivalent
// at complete fillings to expanded marking variants (see BORON-JUNCTIONS.md).
// Learned states restrict the problem; no failure proves the unmarked problem.
import assert from 'node:assert/strict';
export function junctionMarkingClass(Base,nodes,model){
 const byId=new Map(model.candidates.map(c=>[c.id,c])),compiled=nodes.map(n=>({
  point:String(n.point),incident:n.incident.map(e=>typeof e==='string'?e:String(e.candidate).padStart(6,'0')),
  states:n.states.map(s=>(Array.isArray(s)?s:s.candidates).map(id=>typeof id==='string'?id:String(id).padStart(6,'0')))}));
 const touching=new Map();
 for(const [i,n] of compiled.entries()){
  const incident=new Set(n.incident);assert.equal(incident.size,n.incident.length);
  assert.deepEqual([...incident].sort(),model.candidates.filter(c=>c.t.some(x=>x.point===n.point)).map(c=>c.id).sort());
  for(const state of n.states){
   assert.equal(state.length,new Set(state).size);
   assert(state.every(id=>incident.has(id)));
   assert.equal(state.reduce((sum,id)=>sum+byId.get(id).t.find(x=>x.point===n.point).value,0),model.capacity);
  }
  for(const id of incident){if(!touching.has(id))touching.set(id,[]);touching.get(id).push(i);}
 }
 return class JunctionSearch extends Base{
  reason(c){return super.reason(c)||(this.junctionBlocked?.has(c.id)?'learned-junction-marking':null);}
  refresh(_changed){
   this.junctionBlocked=new Set();
   this.junctionDiagnostics??={rebuilds:0,stateTests:0,removed:0};this.junctionDiagnostics.rebuilds++;
   super.refresh(new Set(this.points.keys()));
   // Boolean bit masks: 1 = absent, 2 = present. Propagate both polarities,
   // including mandatory connections implied by every remaining local state.
   const masks=new Map([...touching.keys()].map(id=>[id,this.placed.has(id)?2:this.reasons.get(id)?1:3]));
   const domains=compiled.map(n=>n.states.map(state=>new Set(state)));
   const queue=compiled.map((_,i)=>i),queued=new Set(queue);
   for(let cursor=0;cursor<queue.length;cursor++){
    const i=queue[cursor];queued.delete(i);const node=compiled[i];
    domains[i]=domains[i].filter(state=>{
     this.junctionDiagnostics.stateTests++;
     return node.incident.every(id=>masks.get(id)&(state.has(id)?2:1));
    });
    for(const id of node.incident){
     let supported=0;for(const state of domains[i])supported|=state.has(id)?2:1;
     const next=masks.get(id)&supported;if(next===masks.get(id))continue;
     masks.set(id,next);
     if(!(next&2)&&!this.placed.has(id)&&!this.junctionBlocked.has(id)){
      this.junctionBlocked.add(id);this.junctionDiagnostics.removed++;this.updateCandidate(id);
     }
     for(const j of touching.get(id)||[])if(!queued.has(j)){queued.add(j);queue.push(j);}
    }
   }
   this.junctionMandatory=new Set([...masks].filter(([,bits])=>bits===2).map(([id])=>id));
  }
 };
}

// Independent set-based closure; explicitly reconstructs capacity and markings.
export function independentJunctionDomains(e,model,nodes){
 const selected=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();
 for(const c of model.candidates)if(selected.has(c.id)){
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m||[])marks.set(JSON.stringify([x.point,x.channel??'0']),x.lo);
 }
 const alive=new Set(model.candidates.filter(c=>!selected.has(c.id)&&!e.branchBlocked?.has(c.id)&&
  c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&(c.m||[]).every(x=>{
   const key=JSON.stringify([x.point,x.channel??'0']);return !marks.has(key)||marks.get(key)===x.lo;
  })).map(c=>c.id));
 const convert=id=>typeof id==='string'?id:String(id).padStart(6,'0');
 const tables=nodes.map(n=>({incident:new Set(n.incident.map(x=>convert(typeof x==='string'?x:x.candidate))),
  states:n.states.map(s=>new Set((Array.isArray(s)?s:s.candidates).map(convert)))}));
 for(const table of tables)table.states=table.states.filter(state=>[...table.incident].every(id=>selected.has(id)?state.has(id):alive.has(id)||!state.has(id)));
 const variables=new Set(tables.flatMap(t=>[...t.incident]));
 const relatedById=new Map([...variables].map(id=>[id,[]]));
 for(const table of tables)for(const id of table.incident)relatedById.get(id).push(table);
 let changed=true;
 while(changed){changed=false;
  for(const id of variables){
   const related=relatedById.get(id);let allowed=new Set([false,true]);
   for(const table of related){const values=new Set(table.states.map(s=>s.has(id)));allowed=new Set([...allowed].filter(v=>values.has(v)));}
   for(const table of related){const next=table.states.filter(s=>allowed.has(s.has(id)));if(next.length!==table.states.length){table.states=next;changed=true;}}
   if(!allowed.has(true))alive.delete(id);
  }
 }
 const graph=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates)if(alive.has(c.id))for(const x of c.t)if(graph.has(x.point))graph.get(x.point).set(c.id,x.value);
 return graph;
}
