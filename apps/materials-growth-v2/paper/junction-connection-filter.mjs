// Arc consistency for implicit junction labels with learned pair compatibility.
// A fixed finite projected marking model; absence of a rule is a hypothesis.
import assert from 'node:assert/strict';
const idOf=x=>typeof x==='string'?x:String(x).padStart(6,'0');
export function connectionMarkingClass(Base,nodes,edges,model){
 assert(!model.expand&&model.complete!==false);
 const byId=new Map(model.candidates.map(c=>[c.id,c]));
 const fast=nodes.every(n=>n.states.length<=30),zero=fast?0:0n;
 const bit=i=>fast?2**i:1n<<BigInt(i),full=n=>fast?2**n-1:(1n<<BigInt(n))-1n;
 const tables=nodes.map(n=>{
  const incident=n.incident.map(x=>idOf(typeof x==='string'?x:x.candidate));
  const states=n.states.map(s=>new Set((Array.isArray(s)?s:s.candidates).map(idOf)));
  assert.equal(new Set(states.map(s=>JSON.stringify([...s].sort()))).size,states.length);
  assert.deepEqual([...incident].sort(),model.candidates.filter(c=>c.t.some(x=>x.point===String(n.point))).map(c=>c.id).sort());
  for(const state of states){assert([...state].every(id=>incident.includes(id)));assert.equal([...state].reduce((v,id)=>v+byId.get(id).t.find(x=>x.point===String(n.point)).value,0),model.capacity);}
  return {point:String(n.point),incident,states,full:full(states.length),include:new Map(incident.map(id=>[id,states.reduce((v,s,i)=>s.has(id)?v|bit(i):v,zero)]))};
 });
 const index=new Map(tables.map((n,i)=>[n.point,i])),touching=new Map();
 for(const [i,n] of tables.entries())for(const id of n.incident){if(!touching.has(id))touching.set(id,[]);touching.get(id).push(i);}
 const arcs=[],incoming=tables.map(()=>[]),seen=new Set();
 for(const e of edges){
  const id=idOf(e.candidate),[i,j]=e.points.map(p=>index.get(String(p)));assert(i!==undefined&&j!==undefined&&i!==j&&!seen.has(id));seen.add(id);
  assert.deepEqual([...touching.get(id)].sort(),[i,j].sort());
  const left=tables[i],right=tables[j],forward=left.states.map(s=>s.has(id)?zero:right.full^right.include.get(id)),backward=right.states.map(s=>s.has(id)?zero:left.full^left.include.get(id));
  for(const [a,b] of e.allowedPresentStates){assert(left.states[a].has(id)&&right.states[b].has(id));forward[a]|=bit(b);backward[b]|=bit(a);}
  incoming[j].push(arcs.length);arcs.push({from:i,to:j,support:forward});
  incoming[i].push(arcs.length);arcs.push({from:j,to:i,support:backward});
 }
 for(const [id,at] of touching){assert(at.length<=2);if(at.length===2)assert(seen.has(id));}
 return class ConnectionSearch extends Base{
  reason(c){return super.reason(c)||(this.connectionBlocked?.has(c.id)?'learned-junction-connection':null);}
  refresh(_changed){
   this.connectionBlocked=new Set();this.connectionDiagnostics??={rebuilds:0,arcChecks:0,stateTests:0,removed:0};this.connectionDiagnostics.rebuilds++;
   super.refresh(new Set(this.points.keys()));
   const domains=tables.map(n=>{
    let mask=n.full;for(const id of n.incident){if(this.placed.has(id))mask&=n.include.get(id);else if(this.reasons.get(id))mask&=n.full^n.include.get(id);}return mask;
   });
   const queue=arcs.map((_,i)=>i),queued=new Set(queue);
   for(let cursor=0;cursor<queue.length;cursor++){
    const ai=queue[cursor];queued.delete(ai);const arc=arcs[ai];let next=zero;this.connectionDiagnostics.arcChecks++;
    for(let s=0;s<arc.support.length;s++)if((domains[arc.from]&bit(s))!==zero){this.connectionDiagnostics.stateTests++;if((arc.support[s]&domains[arc.to])!==zero)next|=bit(s);}
    if(next===domains[arc.from])continue;domains[arc.from]=next;
    for(const neighbor of incoming[arc.from])if(!queued.has(neighbor)){queued.add(neighbor);queue.push(neighbor);}
   }
   this.junctionMandatory=new Set();
   for(const [i,n] of tables.entries())for(const id of n.incident){
    const possible=(domains[i]&n.include.get(id))!==zero;
    if(!possible&&!this.placed.has(id)&&!this.connectionBlocked.has(id)){this.connectionBlocked.add(id);this.connectionDiagnostics.removed++;this.updateCandidate(id);}
    if(possible&&(domains[i]&(n.full^n.include.get(id)))===zero)this.junctionMandatory.add(id);
   }
   this.connectionDomains=domains;
  }
 };
}

// Independent sets and synchronous full sweeps instead of bit masks/work queue.
export function independentConnectionDomains(e,model,nodes,edges){
 const selected=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();
 for(const c of model.candidates)if(selected.has(c.id)){
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m||[])marks.set(JSON.stringify([x.point,x.channel??'0']),x.lo);
 }
 const alive=new Set(model.candidates.filter(c=>!selected.has(c.id)&&!e.branchBlocked?.has(c.id)&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&
  (c.m||[]).every(x=>!marks.has(JSON.stringify([x.point,x.channel??'0']))||marks.get(JSON.stringify([x.point,x.channel??'0']))===x.lo)).map(c=>c.id));
 const tables=nodes.map(n=>({point:String(n.point),incident:new Set(n.incident.map(x=>idOf(typeof x==='string'?x:x.candidate))),states:n.states.map(s=>new Set((Array.isArray(s)?s:s.candidates).map(idOf)))}));
 const index=new Map(tables.map((t,i)=>[t.point,i]));
 let domains=tables.map(t=>new Set(t.states.flatMap((s,i)=>[...t.incident].every(id=>selected.has(id)?s.has(id):alive.has(id)||!s.has(id))?[i]:[])));
 const links=edges.map(e=>({...e,candidate:idOf(e.candidate),ij:e.points.map(p=>index.get(String(p))),allowed:new Set(e.allowedPresentStates.map(p=>JSON.stringify(p)))}));
 const compatible=(link,a,b)=>{
  const [i,j]=link.ij,hasA=tables[i].states[a].has(link.candidate),hasB=tables[j].states[b].has(link.candidate);
  return !hasA&&!hasB||(hasA&&hasB&&link.allowed.has(JSON.stringify([a,b])));
 };
 let changed=true;
 while(changed){changed=false;const next=domains.map(s=>new Set(s));
  for(const link of links){const [i,j]=link.ij;
   for(const a of domains[i])if(![...domains[j]].some(b=>compatible(link,a,b)))next[i].delete(a);
   for(const b of domains[j])if(![...domains[i]].some(a=>compatible(link,a,b)))next[j].delete(b);
  }
  changed=next.some((s,i)=>s.size!==domains[i].size);domains=next;
 }
 for(const [i,t] of tables.entries())for(const id of t.incident)if(![...domains[i]].some(s=>t.states[s].has(id)))alive.delete(id);
 const graph=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates)if(alive.has(c.id))for(const x of c.t)if(graph.has(x.point))graph.get(x.point).set(c.id,x.value);
 return {graph,domains};
}
