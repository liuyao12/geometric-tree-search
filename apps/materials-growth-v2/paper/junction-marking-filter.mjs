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
   const queue=compiled.map((_,i)=>i),queued=new Set(queue);
   for(let cursor=0;cursor<queue.length;cursor++){
    const i=queue[cursor];queued.delete(i);const node=compiled[i],selected=node.incident.filter(id=>this.placed.has(id)),supported=new Set();
    for(const state of node.states){
     this.junctionDiagnostics.stateTests++;
     if(!selected.every(id=>state.includes(id)))continue;
     if(state.some(id=>!this.placed.has(id)&&this.reason(this.candidates.get(id))))continue;
     for(const id of state)supported.add(id);
    }
    for(const id of node.incident){
     if(this.placed.has(id)||supported.has(id)||this.junctionBlocked.has(id))continue;
     this.junctionBlocked.add(id);this.junctionDiagnostics.removed++;this.updateCandidate(id);
     for(const j of touching.get(id)||[])if(!queued.has(j)){queued.add(j);queue.push(j);}
    }
   }
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
 let changed=true;
 while(changed){changed=false;
  for(const n of tables){
   const chosen=[...n.incident].filter(id=>selected.has(id)),supported=new Set();
   for(const state of n.states)if(chosen.every(id=>state.has(id))&&[...state].every(id=>selected.has(id)||alive.has(id)))
    for(const id of state)supported.add(id);
   for(const id of n.incident)if(alive.has(id)&&!supported.has(id)){alive.delete(id);changed=true;}
  }
 }
 const graph=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates)if(alive.has(c.id))for(const x of c.t)if(graph.has(x.point))graph.get(x.point).set(c.id,x.value);
 return graph;
}
